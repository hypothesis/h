import copy
import logging

from celery.utils import chunks
from sqlalchemy.orm import load_only

from h.models import Annotation, DocumentURI
from h.schemas.annotation import transform_document
from h.services.annotation_write import AnnotationWriteService
from h.tasks.url_migration import move_annotations
from h.util.uri import normalize

log = logging.getLogger(__name__)


class URLMigrationService:
    """Moves annotations from one URL to another."""

    def __init__(self, request, annotation_write_service: AnnotationWriteService):
        self.request = request
        self._annotation_write_service = annotation_write_service

    def move_annotations(self, annotation_ids, current_uri, new_url_info):
        """
        Migrate a set of annotations to a new URL.

        :param annotation_ids: IDs of annotations to migrate
        :param current_uri: The expected `target_uri` of each annotation.
            This is used to catch cases where the URI changes in between the
            move being scheduled and later executed (eg. via a Celery task).
        :param new_url_info: URL and document metadata to migrate annotations to.
            This is an entry from the mappings defined by the `URLMigrationSchema`
            schema.
        """

        annotations = self.request.db.query(Annotation).filter(
            Annotation.id.in_(annotation_ids)
        )
        current_uri_normalized = normalize(current_uri)

        for ann in annotations:
            if ann.target_uri_normalized != current_uri_normalized:
                # Skip annotation if it was updated since the task was
                # scheduled.
                log.info("Skipping annotation %s", ann.uuid)
                continue

            ann_update_data = {
                "target_uri": new_url_info["url"],
            }

            if "document" in new_url_info:
                ann_update_data["document"] = transform_document(
                    new_url_info["document"], new_url_info["url"]
                )

            # Add selectors to annotation if there is no selector of the same
            # type.
            #
            # This change is specifically to aid in the migration of ebook
            # annotations from a chapter/page URL to the containing book.
            # The information about which chapter/page the annotation refers
            # to is then moved into selectors.
            #
            # See https://github.com/hypothesis/h/issues/7709
            if new_selectors := new_url_info.get("selectors"):
                selectors = copy.deepcopy(ann.target_selectors)
                for new_sel in new_selectors:
                    if not any(s for s in selectors if s["type"] == new_sel["type"]):
                        selectors.append(new_sel)
                ann_update_data["target_selectors"] = selectors

            # Update the annotation's `target_uri` and associated document,
            # and create `Document*` entities for the new URL if they don't
            # already exist.
            self._annotation_write_service.update_annotation(
                annotation=ann,
                data=ann_update_data,
                # Don't update "edited" timestamp on annotation cards.
                update_timestamp=False,
                reindex_tag="URLMigrationService.move_annotations",
                # This action is taken by the admin user most of the time, who
                # will not have write permission in the relevant group, so we
                # disable the check
                enforce_write_permission=False,
            )

            log.info("Moved annotation %s to URL %s", ann.uuid, ann.target_uri)

    def move_annotations_by_url(self, url, new_url_info):
        """
        Find annotations with a given target URL and move them to another URL.

        :param url: The current URL of the annotations
        :param new_url_info: The URL and document metadata of the new URL.
             This is an entry matching the `URLMigrationSchema` schema.
        """

        session = self.request.db
        uri_normalized = normalize(url)

        # Get the IDs of all annotations on the old URL, and divide into
        # fixed-sized batches. A separate Celery task is then launched per
        # batch to migrate those annotations. This limits the amount of
        # work per task in case there are a large number of annotations on
        # a given URL.
        annotations = (
            session.query(Annotation)
            .join(DocumentURI, Annotation.document_id == DocumentURI.document_id)
            .filter(DocumentURI.uri_normalized == uri_normalized)
            .options(load_only(Annotation.id, Annotation.target_uri))
        )

        ann_ids = [ann.id for ann in annotations]

        if not ann_ids:
            return

        # Move the first matching annotation. This will create the
        # document-related entities for the new URL if they don't already exist,
        # This avoids errors related to concurrent document URL/metadata updates
        # when the remaining annotations are moved in parallel.
        first_ann = ann_ids[0]
        self.move_annotations([first_ann], url, new_url_info)

        # Ensure new document is visible in tasks that move remaining
        # annotations.
        self.request.tm.commit()

        # Schedule async tasks to move the remaining annotations.
        ann_ids = ann_ids[1:]
        anns_per_batch = 50
        for batch in chunks(iter(ann_ids), anns_per_batch):
            move_annotations.delay(batch, url, new_url_info)

        log.info(
            "Migrating %s annotations from %s to %s",
            len(ann_ids) + 1,
            url,
            new_url_info["url"],
        )


def service_factory(_context, request):
    return URLMigrationService(
        request=request,
        annotation_write_service=request.find_service(AnnotationWriteService),
    )

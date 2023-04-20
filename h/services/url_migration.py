import copy
import logging

from celery.utils import chunks

from h.schemas.annotation import transform_document
from h.services.annotation_read import AnnotationReadService
from h.tasks.url_migration import move_annotations

log = logging.getLogger(__name__)


class URLMigrationService:
    """Moves annotations from one URL to another."""

    BATCH_SIZE = 50
    """How many annotations to migrate at once."""

    def __init__(
        self, transaction_manager, annotation_read_service: AnnotationReadService
    ):
        self._transaction_manager = transaction_manager
        self._annotation_read_service = annotation_read_service

    def move_annotations(self, annotation_ids, current_uri, new_url_info):
        """
        Migrate a set of annotations to a new URL.

        :param annotation_ids: IDs of annotations to migrate
        :param current_uri: The expected `target_uri` of each annotation.
            This is used to catch cases where the URI changes in between the
            move being scheduled and later executed (e.g. via a Celery task).
        :param new_url_info: URL and document metadata to migrate annotations
            to. This is an entry from the mappings defined by the
            `URLMigrationSchema` schema.
        """

        # Skip annotation if it was updated since the task was scheduled
        for annotation in self._annotation_read_service.search_annotations(
            ids=annotation_ids, target_uri=current_uri
        ):
            update_data = {"target_uri": new_url_info["url"]}

            if "document" in new_url_info:
                update_data["document"] = transform_document(
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
                selectors = copy.deepcopy(annotation.target_selectors)
                existing_types = {selector["type"] for selector in selectors}

                selectors.extend(
                    selector
                    for selector in new_selectors
                    if selector["type"] not in existing_types
                )

                update_data["target_selectors"] = selectors

            # Update the annotation's `target_uri` and associated document,
            # and create `Document*` entities for the new URL if they don't
            # already exist.
            self._annotation_read_service.update_annotation(
                annotation,
                update_data,
                # Don't update "edited" timestamp on annotation cards.
                update_timestamp=False,
                reindex_tag="URLMigrationService.move_annotations",
            )

            log.info(
                "Moved annotation %s to URL %s", annotation.uuid, annotation.target_uri
            )

    def move_annotations_by_url(self, url, new_url_info):
        """
        Find annotations with a given target URL and move them to another URL.

        :param url: The current URL of the annotations
        :param new_url_info: The URL and document metadata of the new URL.
             This is an entry matching the `URLMigrationSchema` schema.
        """
        # Get the IDs of all annotations on the old URL
        annotations = self._annotation_read_service.search_annotations(document_uri=url)
        annotation_ids = [annotation.id for annotation in annotations]
        if not annotation_ids:
            return

        # Move the one matching annotation first to create the document-related
        # entities for the new URL if they don't already exist. This avoids
        # errors related to concurrent document URL/metadata updates when the
        # remaining annotations are moved in parallel.
        self.move_annotations([annotation_ids.pop()], url, new_url_info)

        # Ensure new document is visible in tasks that move remaining
        # annotations.
        self._transaction_manager.commit()

        # Schedule async tasks to move the remaining annotations in chunks
        for batch in chunks(iter(annotation_ids), n=self.BATCH_SIZE):
            move_annotations.delay(batch, url, new_url_info)

        log.info(
            "Migrating %s annotations from %s to %s",
            len(annotation_ids) + 1,
            url,
            new_url_info["url"],
        )


def url_migration_factory(_context, request):
    return URLMigrationService(
        transaction_manager=request.tm,
        annotation_read_service=request.find_service(AnnotationReadService),
    )

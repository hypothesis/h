from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy.orm import subqueryload

from h import i18n
from h.db.types import InvalidUUID
from h.models import Annotation
from h.models.document import update_document_metadata
from h.schemas import ValidationError
from h.util.group_scope import url_in_scope

_ = i18n.TranslationStringFactory(__package__)


class AnnotationService:
    def __init__(self, db_session, search_index_service):
        self._db = db_session
        self._search_index_service = search_index_service

    def get_annotations_by_id(
        self, ids: List[str], eager_load: Optional[List] = None
    ) -> Iterable[Annotation]:
        """
        Get annotations in the same order as the provided ids.

        :param ids: the list of annotation ids
        :param eager_load: A list of annotatiopn relationships to eager load
            like `Annotation.document`
        """

        if not ids:
            return []

        query = self._db.query(Annotation).filter(Annotation.id.in_(ids))

        if eager_load:
            query = query.options(subqueryload(prop) for prop in eager_load)

        return sorted(query, key=lambda annotation: ids.index(annotation.id))

    def update_annotation(
        self,
        annotation: Annotation,
        data: dict,
        update_timestamp: bool = True,
        reindex_tag: str = "storage.update_annotation",
    ) -> Annotation:
        """
        Update an existing annotation and its associated document metadata.

        :param id_: ID of the annotation to be updated, this is assumed to be a
            validated ID of an annotation that does already exist in the
            database
        :param data: Validated data with which to update the annotation
        :param update_timestamp: Whether to update the last-edited timestamp of
            the annotation.
        :param reindex_tag: Tag used by the reindexing job to identify the
            source of the reindexing request.
        """
        initial_target_uri = annotation.target_uri

        self._update_annotation_values(annotation, data)
        if update_timestamp:
            annotation.updated = datetime.utcnow()

        # Expire the group relationship, so we get the most up-to-date value
        # instead of the one which was present when we loaded the model
        # https://docs.sqlalchemy.org/en/13/faq/sessions.html#i-set-the-foo-id-attribute-on-my-instance-to-7-but-the-foo-attribute-is-still-none-shouldn-t-it-have-loaded-foo-with-id-7
        self._db.expire(annotation, ["group"])
        self._validate_group(annotation)

        if (
            document := data.get("document", {})
        ) or annotation.target_uri != initial_target_uri:
            annotation.document = update_document_metadata(
                self._db,
                annotation.target_uri,
                document.get("document_meta_dicts", {}),
                document.get("document_uri_dicts", {}),
                updated=annotation.updated,
            )

        # The search index service by default does not reindex if the existing ES
        # entry's timestamp matches the DB timestamp. If we're not changing this
        # timestamp, we need to force reindexing.
        self._search_index_service._queue.add_by_id(  # pylint: disable=protected-access
            annotation.id, tag=reindex_tag, schedule_in=60, force=not update_timestamp
        )

        return annotation

    @staticmethod
    def _update_annotation_values(annotation: Annotation, data: dict):
        for key, value in data.items():
            # Don't set complex things
            if key in ("document", "extra"):
                continue

            setattr(annotation, key, value)

        extra = data.get("extra", {})
        annotation.extra.update(extra)

    @staticmethod
    def _validate_group(annotation: Annotation):
        group = annotation.group
        if not group:
            raise ValidationError(
                "group: " + _(f"Invalid group id {annotation.groupid}")
            )

        # If no scopes are present, or if the group is configured to allow
        # annotations outside its scope, there's nothing to do here
        if not group.scopes or not group.enforce_scope:
            return

        # The target URI must match at least one
        # of a group's defined scopes, if the group has any
        if not url_in_scope(
            annotation.target_uri, [scope.scope for scope in group.scopes]
        ):
            raise ValidationError(
                "group scope: "
                + _("Annotations for this target URI are not allowed in this group")
            )


def service_factory(_context, request):
    return AnnotationService(
        db_session=request.db,
        search_index_service=request.find_service(  # pylint: disable=protected-access
            name="search_index"
        ),
    )

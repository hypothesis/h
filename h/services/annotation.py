from datetime import datetime
from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Query, Session, subqueryload

from h import i18n
from h.models import Annotation, DocumentURI
from h.models.document import update_document_metadata
from h.schemas import ValidationError
from h.services.search_index import SearchIndexService
from h.util.group_scope import url_in_scope
from h.util.uri import normalize

_ = i18n.TranslationStringFactory(__package__)


class AnnotationService:
    """A service for storing and retrieving annotations."""

    def __init__(self, db_session: Session, search_index_service: SearchIndexService):
        self._db = db_session
        self._search_index_service = search_index_service

    def get_annotations_by_id(
        self, ids: List[str], eager_load: Optional[List] = None
    ) -> Iterable[Annotation]:
        """
        Get annotations in the same order as the provided ids.

        :param ids: the list of annotation ids
        :param eager_load: A list of annotation relationships to eager load
            like `Annotation.document`
        """

        if not ids:
            return []

        annotations = self._db.execute(
            self._annotation_search_query(ids=ids, eager_load=eager_load)
        ).scalars()

        return sorted(annotations, key=lambda annotation: ids.index(annotation.id))

    def search_annotations(
        self,
        ids: Optional[List[str]] = None,
        target_uri: Optional[str] = None,
        document_uri: Optional[str] = None,
    ) -> Iterable[Annotation]:
        """
        Search for annotations using information stored in Postgres.

        :param ids: Search by specified annotation ids
        :param target_uri: Search by annotation target URI
        :param document_uri: Search by document URI
        """
        query = self._annotation_search_query(
            ids=ids, document_uri=document_uri, target_uri=target_uri
        )

        return self._db.execute(query).scalars().all()

    def update_annotation(
        self,
        annotation: Annotation,
        data: dict,
        update_timestamp: bool = True,
        reindex_tag: str = "storage.update_annotation",
    ) -> Annotation:
        """
        Update an annotation and its associated document metadata.

        :param annotation: Annotation to be updated
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

    @staticmethod
    def _annotation_search_query(
        ids: Optional[List[str]] = None,
        document_uri: Optional[str] = None,
        target_uri: Optional[str] = None,
        eager_load: Optional[List] = None,
    ) -> Query:
        """Create a query for searching for annotations."""

        query = select(Annotation)

        if ids:
            query = query.where(Annotation.id.in_(ids))

        if target_uri:
            query = query.where(
                Annotation.target_uri_normalized == normalize(target_uri)
            )

        if document_uri:
            document_subquery = select(DocumentURI.document_id).where(
                DocumentURI.uri_normalized == normalize(document_uri)
            )
            query = query.where(Annotation.document_id.in_(document_subquery))

        if eager_load:
            query = query.options(subqueryload(*eager_load))

        return query


def service_factory(_context, request) -> AnnotationService:
    """Get an annotation service instance."""

    return AnnotationService(
        db_session=request.db,
        search_index_service=request.find_service(  # pylint: disable=protected-access
            name="search_index"
        ),
    )

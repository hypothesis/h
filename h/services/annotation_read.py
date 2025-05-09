from collections.abc import Iterable

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, subqueryload

from h.db.types import InvalidUUID
from h.models import Annotation, ModerationStatus


class AnnotationReadService:
    """A service for storing and retrieving annotations."""

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_annotation_by_id(self, id_: str) -> Annotation | None:
        """
        Fetch the annotation with the given id.

        :param id_: Annotation ID to retrieve
        """
        try:
            return self._db.get(Annotation, id_)
        except InvalidUUID:
            return None

    def get_annotations_by_id(
        self, ids: list[str], eager_load: list | None = None
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
            self.annotation_search_query(
                ids=ids,
                eager_load=eager_load,
                include_deleted=True,
                include_private=True,
            )
        ).scalars()

        return sorted(annotations, key=lambda annotation: ids.index(annotation.id))

    @staticmethod
    def annotation_search_query(  # noqa: PLR0913
        ids: list[str] | None = None,
        *,
        eager_load: list | None = None,
        groupid: str | None = None,
        include_private: bool = False,
        include_deleted: bool = False,
        moderation_status: ModerationStatus | None = None,
    ) -> Select[tuple[Annotation]]:
        """Create a query for searching for annotations."""

        query = select(Annotation)

        if not include_deleted:
            query = query.where(Annotation.deleted.is_(False))

        if not include_private:
            query = query.where(Annotation.shared.is_(True))

        if ids:
            query = query.where(Annotation.id.in_(ids))

        if groupid:
            query = query.where(Annotation.groupid == groupid)

        if moderation_status:
            if moderation_status == ModerationStatus.APPROVED:
                # We have not migrated all annotations to have a moderation status
                # APPROVED is implicit when no moderation status is set
                query = query.where(
                    or_(
                        Annotation.moderation_status.is_(None),
                        Annotation.moderation_status == ModerationStatus.APPROVED,
                    )
                )
            else:
                query = query.where(Annotation.moderation_status == moderation_status)

        if eager_load:
            query = query.options(*(subqueryload(prop) for prop in eager_load))

        return query

    @staticmethod
    def count_query(query: Select[tuple[Annotation]]) -> Select[tuple[int]]:
        """Convert an annotations query into a count of annotations."""

        return query.with_only_columns(func.count(Annotation.id))


def service_factory(_context, request) -> AnnotationReadService:
    """Get an annotation service instance."""

    return AnnotationReadService(db_session=request.db)

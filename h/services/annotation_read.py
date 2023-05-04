from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Query, Session, subqueryload

from h.db.types import InvalidUUID
from h.models import Annotation


class AnnotationReadService:
    """A service for storing and retrieving annotations."""

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_annotation_by_id(self, id_: str) -> Optional[Annotation]:
        """
        Fetch the annotation with the given id.

        :param id_: Annotation ID to retrieve
        """
        try:
            return self._db.query(Annotation).get(id_)
        except InvalidUUID:
            return None

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

    @staticmethod
    def _annotation_search_query(
        ids: List[str] = None, eager_load: Optional[List] = None
    ) -> Query:
        """Create a query for searching for annotations."""

        query = select(Annotation)
        query = query.where(Annotation.id.in_(ids))

        if eager_load:
            query = query.options(*(subqueryload(prop) for prop in eager_load))

        return query


def service_factory(_context, request) -> AnnotationReadService:
    """Get an annotation service instance."""

    return AnnotationReadService(db_session=request.db)

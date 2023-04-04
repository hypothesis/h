from typing import Iterable, List, Optional

from sqlalchemy.orm import Session, subqueryload

from h.models import Annotation


class AnnotationService:
    """A service for storing and retrieving annotations."""

    def __init__(self, db_session: Session):
        self._db = db_session

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

        query = self._db.query(Annotation).filter(Annotation.id.in_(ids))

        if eager_load:
            query = query.options(subqueryload(prop) for prop in eager_load)

        return sorted(query, key=lambda annotation: ids.index(annotation.id))


def service_factory(_context, request) -> AnnotationService:
    """Get an annotation service instance."""

    return AnnotationService(db_session=request.db)

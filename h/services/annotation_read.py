from typing import Optional

from sqlalchemy.orm import Session

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


def service_factory(_context, request) -> AnnotationReadService:
    """Get an annotation service instance."""

    return AnnotationReadService(db_session=request.db)

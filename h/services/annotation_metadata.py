import json

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from h.models import Annotation, AnnotationMetadata, AnnotationSlim


class AnnotationMetadataService:
    def __init__(self, db: Session):
        self._db = db

    def set(self, annotation: Annotation, data: dict):
        """Set `data` as the  `annotation`'s metadata."""
        stmt = insert(AnnotationMetadata).from_select(
            ["annotation_id", "data"],
            select(
                # Select annotation_slim.id via the JOIN
                AnnotationSlim.id,
                # Just use a literal for the actual data
                func.jsonb(json.dumps(data)),
            )
            .join(Annotation)
            .where(Annotation.id == annotation.id),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["annotation_id"],
            set_={"data": stmt.excluded.data},
        )
        self._db.execute(stmt)


def factory(_context, request) -> AnnotationMetadataService:
    return AnnotationMetadataService(db=request.db)

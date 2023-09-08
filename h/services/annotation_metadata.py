import os

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from h.models import Annotation, AnnotationMetadata
from h.security import decrypt_jwe_dict


class AnnotationMetadataService:
    def __init__(self, db: Session):
        self._db = db
        self._secret = os.environ.get("JWE_SECRET_LMS")

    def set_annotation_metadata_from_jwe(self, annotation: Annotation, jwe: str):
        annotation_metadata = decrypt_jwe_dict(self._secret, jwe)

        self._set_annotation_metadata(annotation, annotation_metadata)
        return annotation_metadata

    def _set_annotation_metadata(self, annotation, metadata: dict):
        stmt = insert(AnnotationMetadata).values(
            [{"annotation_pk": annotation.pk, "data": metadata}]
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["annotation_pk"],
            set_={"data": stmt.excluded.data},
        )
        self._db.execute(stmt)


def factory(_context, request) -> AnnotationMetadataService:
    return AnnotationMetadataService(db=request.db)

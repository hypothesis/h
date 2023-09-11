import json
import os

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from h.models import Annotation, AnnotationMetadata, AnnotationSlim
from h.security import decrypt_jwe_dict


class AnnotationMetadataService:
    def __init__(self, db: Session):
        self._db = db
        self._secret = os.environ.get("JWE_SECRET_LMS")

    def set_annotation_metadata_from_jwe(self, annotation: Annotation, jwe: str):
        """
        Set the decrypted `jwe` dict as the metadata for `annotation`.

        It will create a new AnnotationMetadata row or update the existing one.
        """
        annotation_metadata = decrypt_jwe_dict(self._secret, jwe)

        self._set_annotation_metadata(annotation, annotation_metadata)
        return annotation_metadata

    def _set_annotation_metadata(self, annotation: Annotation, metadata: dict):
        stmt = insert(AnnotationMetadata).from_select(
            ["annotation_id", "data"],
            select(
                # Select annotation_slim.id via the JOIN
                AnnotationSlim.id,
                # Just use a literal for the actual data
                func.jsonb(json.dumps(metadata)),
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

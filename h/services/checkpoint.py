from datetime import datetime

from sqlalchemy import or_, select

from h.models import Checkpoint, Document


class CheckpointService:
    """Resolve Hide & Reveal checkpoints for annotation-search authorization."""

    def __init__(self, db):
        self.db = db

    def active_checkpoint(self, group_id: int, uri: str) -> Checkpoint | None:
        """
        Return an active (unrevealed) checkpoint for `(group_id, uri)`, or None.

        The `uri` is resolved to its Document(s) the same way the search layer
        resolves the request's `uri` param, so the checkpoint lookup matches the
        annotations the search will return even when the same document is
        addressed by an equivalent URI (e.g. a PDF fingerprint).

        A checkpoint is "active" (still hiding annotations) when its reveal_date
        has not yet passed: it is NULL (never revealed) or in the future.
        """
        document_ids = [doc.id for doc in Document.find_by_uris(self.db, [uri])]
        if not document_ids:
            return None

        return self.db.scalar(
            select(Checkpoint)
            .where(Checkpoint.group_id == group_id)
            .where(Checkpoint.document_id.in_(document_ids))
            .where(
                or_(
                    Checkpoint.reveal_date.is_(None),
                    Checkpoint.reveal_date > datetime.utcnow(),  # noqa: DTZ003
                )
            )
            .limit(1)
        )


def factory(_context, request) -> CheckpointService:
    """Return a CheckpointService instance for the passed context and request."""
    return CheckpointService(db=request.db)

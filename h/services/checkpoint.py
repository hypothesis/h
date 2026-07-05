from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_, select

from h.models import (
    Annotation,
    Checkpoint,
    Document,
    DocumentURI,
    GroupMembership,
    User,
)
from h.models.group import LMSRole


@dataclass
class HiddenScope:
    """A (group, document) under an active checkpoint, with its visibility data."""

    group_pubid: str
    document_id: int
    uris: list[str]
    instructor_userids: list[str]
    own_annotation_ids: list[str]


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

    def hidden_scopes(self, user: User | None) -> list[HiddenScope]:
        """
        Return the scopes whose annotations must be hidden from user.

        An empty list (the common case: a user with no active checkpoints) means
        search behaves normally.
        """
        if user is None:
            return []

        checkpoints = self.db.scalars(
            select(Checkpoint)
            .join(GroupMembership, GroupMembership.group_id == Checkpoint.group_id)
            .where(GroupMembership.user_id == user.id)
            .where(
                or_(
                    GroupMembership.lms_role.is_(None),
                    GroupMembership.lms_role != LMSRole.LMS_INSTRUCTOR.value,
                )
            )
            .where(
                or_(
                    Checkpoint.reveal_date.is_(None),
                    Checkpoint.reveal_date > datetime.utcnow(),  # noqa: DTZ003
                )
            )
        ).all()

        return [self._hidden_scope(user, checkpoint) for checkpoint in checkpoints]

    def hides_annotation(self, user: User | None, annotation: Annotation) -> bool:
        """
        Return True if `annotation` must be hidden from `user` by a checkpoint.

        This is the per-annotation form of the search-time HideRevealFilter rule,
        for read paths that handle one annotation at a time (e.g. the realtime
        streamer). An annotation in an active hidden scope is hidden unless it is
        the user's own, an instructor note, or an instructor reply to one of the
        user's own annotations. Instructors and users with no active checkpoints
        see everything.
        """
        if user is None:
            return False

        for scope in self.hidden_scopes(user):
            if (
                annotation.groupid != scope.group_pubid
                or annotation.document_id != scope.document_id
            ):
                continue

            # In scope: hidden unless it is in the visible set (the user's own
            # annotation, an instructor note, or an instructor reply to one of
            # the user's own annotations).
            if annotation.userid == user.userid:
                return False
            return not (
                annotation.userid in scope.instructor_userids
                and (
                    not annotation.references
                    or set(annotation.references) & set(scope.own_annotation_ids)
                )
            )

        return False

    def _hidden_scope(self, user: User, checkpoint: Checkpoint) -> HiddenScope:
        group_pubid = checkpoint.group.pubid

        uris = self.db.scalars(
            select(DocumentURI.uri_normalized).where(
                DocumentURI.document_id == checkpoint.document_id
            )
        ).all()

        # User.userid is a hybrid that compiles to a tuple, so it can't be
        # SELECTed directly: load the users and read it in Python.
        instructors = self.db.scalars(
            select(User)
            .join(GroupMembership, GroupMembership.user_id == User.id)
            .where(GroupMembership.group_id == checkpoint.group_id)
            .where(GroupMembership.lms_role == LMSRole.LMS_INSTRUCTOR.value)
        ).all()
        instructor_userids = [instructor.userid for instructor in instructors]

        own_annotation_ids = self.db.scalars(
            select(Annotation.id)
            .where(Annotation.userid == user.userid)
            .where(Annotation.groupid == group_pubid)
        ).all()

        return HiddenScope(
            group_pubid=group_pubid,
            document_id=checkpoint.document_id,
            uris=list(uris),
            instructor_userids=instructor_userids,
            own_annotation_ids=list(own_annotation_ids),
        )


def factory(_context, request) -> CheckpointService:
    """Return a CheckpointService instance for the passed context and request."""
    return CheckpointService(db=request.db)

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert

from h.models import (
    Annotation,
    Checkpoint,
    Document,
    DocumentURI,
    Group,
    GroupMembership,
    User,
)
from h.models.group import LMSRole
from h.schemas import ValidationError


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

    def upsert_checkpoint(
        self,
        authority: str,
        group_authority_provided_id: str,
        document_uri: str,
        reveal_date: str | None = None,
    ) -> Checkpoint | None:
        """
        Upsert a checkpoint for a (group, document) pair.

        Resolves the group by authority + authority_provided_id and the
        document by URI. Creates the document if it doesn't exist yet.

        Returns the upserted Checkpoint, or None if the group or document
        could not be resolved.
        """
        group = self.db.scalar(
            select(Group).where(
                Group.authority == authority,
                Group.authority_provided_id == group_authority_provided_id,
            )
        )
        if not group:
            return None

        document = Document.find_or_create_by_uris(
            self.db, claimant_uri=document_uri, uris=[]
        ).first()
        if not document:
            return None

        parsed_reveal_date = None
        if reveal_date:
            try:
                parsed_reveal_date = datetime.fromisoformat(reveal_date)
            except ValueError as err:
                msg = f"Invalid reveal_date: {reveal_date!r}"
                raise ValidationError(msg) from err
            # Store naive UTC to match the column and the utcnow() comparisons.
            if parsed_reveal_date.tzinfo is not None:
                parsed_reveal_date = parsed_reveal_date.astimezone(UTC).replace(
                    tzinfo=None
                )

        stmt = (
            insert(Checkpoint)
            .values(
                group_id=group.id,
                document_id=document.id,
                previous_checkpoint_id=None,
                reveal_date=parsed_reveal_date,
            )
            # If a checkpoint already exists for this (group, document), update the
            # reveal_date. coalesce keeps the existing date if the new one is NULL.
            .on_conflict_do_update(
                constraint="uq__checkpoint__group_id__document_id__previous_checkpoint_id",
                set_={
                    "reveal_date": func.coalesce(
                        parsed_reveal_date, Checkpoint.reveal_date
                    )
                },
            )
            .returning(Checkpoint.id)
        )
        result = self.db.execute(stmt)
        self.db.flush()

        checkpoint_id = result.scalar()
        return self.db.get(Checkpoint, checkpoint_id)

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

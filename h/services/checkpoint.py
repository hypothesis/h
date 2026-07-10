from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar

from sqlalchemy import or_, select
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
from h.util.uri import build_scope_key


@dataclass
class HiddenScope:
    """A (group, document) under an active checkpoint, with its visibility data."""

    group_pubid: str
    document_id: int
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

    _ROLE_MAP: ClassVar[dict[str, LMSRole]] = {
        "instructor": LMSRole.LMS_INSTRUCTOR,
        "student": LMSRole.LMS_STUDENT,
    }

    def set_user_role(
        self,
        authority: str,
        username: str,
        role: str,
        group_authority_provided_ids: list[str],
    ) -> None:
        """Set the lms_role for a user in the given groups."""
        lms_role = self._ROLE_MAP.get(role)
        if not lms_role:
            return

        user = User.get_by_username(self.db, username, authority)
        if not user:
            return

        memberships = self.db.scalars(
            select(GroupMembership)
            .join(Group, Group.id == GroupMembership.group_id)
            .where(GroupMembership.user_id == user.id)
            .where(Group.authority == authority)
            .where(Group.authority_provided_id.in_(group_authority_provided_ids))
        ).all()

        for membership in memberships:
            membership.lms_role = lms_role.value

    def upsert_checkpoint(
        self,
        authority: str,
        group_authority_provided_id: str,
        document_uri: str,
    ) -> Checkpoint | None:
        """
        Upsert a checkpoint for a (group, document) pair.

        Resolves the group by authority + authority_provided_id and
        resolves-or-creates the document by URI. If the checkpoint already
        exists, it is not modified.

        Returns the Checkpoint, or None if the group could not be resolved.
        """
        group = self.db.scalar(
            select(Group).where(
                Group.authority == authority,
                Group.authority_provided_id == group_authority_provided_id,
            )
        )
        if not group:
            return None

        # Resolve-or-create the document. A checkpoint is synced at
        # assignment-launch time, before anyone has annotated the URL, so its
        # Document may not exist yet. Creating it (with document_uri as a
        # self-claim) means a later annotation on that URL resolves onto the
        # same Document, so the checkpoint hides annotations from the first one.
        document = Document.find_or_create_by_uris(self.db, document_uri, []).first()

        stmt = (
            insert(Checkpoint)
            .values(
                group_id=group.id,
                document_id=document.id,
                previous_checkpoint_id=None,
            )
            .on_conflict_do_nothing(
                constraint="uq__checkpoint__group_id__document_id__previous_checkpoint_id",
            )
            .returning(Checkpoint.id)
        )
        result = self.db.execute(stmt)
        self.db.flush()

        checkpoint_id = result.scalar()
        if checkpoint_id:
            # New checkpoint was inserted.
            return self.db.get(Checkpoint, checkpoint_id)

        # Checkpoint already existed — on_conflict_do_nothing doesn't return
        # the existing row, so we need a separate query to fetch it.
        return self.db.scalar(
            select(Checkpoint).where(
                Checkpoint.group_id == group.id,
                Checkpoint.document_id == document.id,
            )
        )

    def reveal_checkpoint(
        self,
        authority: str,
        group_authority_provided_id: str,
        document_uri: str,
    ) -> Checkpoint | None:
        """
        Reveal a checkpoint by setting its reveal_date to now.

        Returns the updated Checkpoint, or None if not found.
        """
        group = self.db.scalar(
            select(Group).where(
                Group.authority == authority,
                Group.authority_provided_id == group_authority_provided_id,
            )
        )
        if not group:
            return None

        document_ids = [
            doc.id for doc in Document.find_by_uris(self.db, [document_uri])
        ]
        if not document_ids:
            return None

        checkpoint = self.db.scalar(
            select(Checkpoint)
            .where(Checkpoint.group_id == group.id)
            .where(Checkpoint.document_id.in_(document_ids))
            .where(
                or_(
                    Checkpoint.reveal_date.is_(None),
                    Checkpoint.reveal_date > datetime.utcnow(),  # noqa: DTZ003
                )
            )
            .limit(1)
        )
        if not checkpoint:
            return None

        checkpoint.reveal_date = datetime.utcnow()  # noqa: DTZ003
        self.db.flush()
        return checkpoint

    def scope_keys(self, group_pubid: str, document_id: int) -> list[str]:
        """
        Return every `target.scope` value an in-scope annotation can carry.

        An annotation indexes a single scope key: its normalized target URI,
        suffixed with `__v<version>` when it annotates a specific document
        version (see `build_scope_key`). Enumerating them all lets the search
        filter match with one `terms` clause, which costs one clause against
        Elasticsearch's 1024-clause budget however many URIs it holds. Matching
        a wildcard per URI instead exhausts that budget on a document that has
        accumulated many URIs, and Elasticsearch then rejects the whole query.

        Versions are looked up within `group_pubid`: the filter only ever
        matches annotations in that group, so a version used nowhere in it
        cannot match, and `annotation.groupid` is indexed where
        `annotation.document_id` is not.
        """
        # Distinct: a document has one document_uri row per (uri, type,
        # content_type), so the same uri_normalized repeats many times over.
        uris = self.db.scalars(
            select(DocumentURI.uri_normalized)
            .where(DocumentURI.document_id == document_id)
            .distinct()
        ).all()

        versions = self.db.scalars(
            select(Annotation.version)
            .where(Annotation.groupid == group_pubid)
            .where(Annotation.document_id == document_id)
            .where(Annotation.version.is_not(None))
            .distinct()
        ).all()

        keys = [
            build_scope_key(uri_normalized, version)
            for uri_normalized in uris
            for version in [None, *versions]
        ]
        # build_scope_key(uri, 0) is just uri, so versions can collide.
        return list(dict.fromkeys(keys))

    def _hidden_scope(self, user: User, checkpoint: Checkpoint) -> HiddenScope:
        group_pubid = checkpoint.group.pubid

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
            instructor_userids=instructor_userids,
            own_annotation_ids=list(own_annotation_ids),
        )


def factory(_context, request) -> CheckpointService:
    """Return a CheckpointService instance for the passed context and request."""
    return CheckpointService(db=request.db)

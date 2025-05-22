from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from h.db import Base, types
from h.models.group import Group
from h.util import markdown_render, uri
from h.util.user import split_user

if TYPE_CHECKING:
    from h.models.moderation_log import ModerationLog


class ModerationStatus(Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    DENIED = "DENIED"
    SPAM = "SPAM"


class Annotation(Base):
    """Model class representing a single annotation."""

    __tablename__ = "annotation"
    __table_args__ = (
        # Tags are stored in an array-type column, and indexed using a
        # generalised inverted index. For more information on the use of GIN
        # indices for array columns, see:
        #
        #   http://www.databasesoup.com/2015/01/tag-all-things.html
        #   http://www.postgresql.org/docs/9.5/static/gin-intro.html
        #
        sa.Index("ix__annotation_tags", "tags", postgresql_using="gin"),
        sa.Index("ix__annotation_created", "created"),
        sa.Index("ix__annotation_updated", "updated"),
        # This is a functional index on the *first* of the annotation's
        # references, pointing to the top-level annotation it refers to. We're
        # using 1 here because Postgres uses 1-based array indexing.
        sa.Index("ix__annotation_thread_root", sa.text('("references"[1])')),
    )

    #: Annotation ID: these are stored as UUIDs in the database, and mapped
    #: transparently to a URL-safe Base64-encoded string.

    id: Mapped[str] = mapped_column(
        types.URLSafeUUID, server_default=sa.func.uuid_generate_v1mc(), primary_key=True
    )

    #: The timestamp when the annotation was created.
    created: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, server_default=sa.func.now()
    )

    #: The timestamp when the user edited the annotation last.
    updated: Mapped[datetime] = mapped_column(
        server_default=sa.func.now(), default=datetime.utcnow
    )

    #: The full userid (e.g. 'acct:foo@example.com') of the owner of this
    #: annotation.
    userid = sa.Column(sa.UnicodeText, nullable=False, index=True)
    #: The string id of the group in which this annotation is published.
    #: Defaults to the global public group, "__world__".
    groupid = sa.Column(
        sa.UnicodeText,
        default="__world__",
        server_default="__world__",
        nullable=False,
        index=True,
    )

    group = relationship(
        Group,
        primaryjoin=(Group.pubid == groupid),
        foreign_keys=[groupid],
        lazy="select",
    )

    #: The textual body of the annotation.
    _text = sa.Column("text", sa.UnicodeText)
    #: The Markdown-rendered and HTML-sanitized textual body of the annotation.
    _text_rendered = sa.Column("text_rendered", sa.UnicodeText)

    #: The tags associated with the annotation.
    tags = sa.Column(
        MutableList.as_mutable(pg.ARRAY(sa.UnicodeText, zero_indexes=True))
    )

    #: A boolean indicating whether this annotation is shared with members of
    #: the group it is published in. "Private"/"Only me" annotations have
    #: shared=False.
    shared = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    #: The URI of the annotated page, as provided by the client.
    _target_uri = sa.Column("target_uri", sa.UnicodeText)
    #: The URI of the annotated page in normalized form.
    _target_uri_normalized = sa.Column("target_uri_normalized", sa.UnicodeText)
    #: The serialized selectors for the annotation on the annotated page.
    target_selectors = sa.Column(
        types.AnnotationSelectorJSONB, default=list, server_default=sa.func.jsonb("[]")
    )

    #: An array of annotation IDs which are ancestors of this annotation.
    references: Mapped[list[str] | None] = mapped_column(
        pg.ARRAY(types.URLSafeUUID, zero_indexes=True),
        default=list,
        server_default=sa.text("ARRAY[]::uuid[]"),
    )

    #: Any additional serialisable data provided by the client.
    extra: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(pg.JSONB()),
        default=dict,
        server_default=sa.func.jsonb("{}"),
    )

    #: Has the annotation been deleted?
    deleted = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    document_id = sa.Column(sa.Integer, sa.ForeignKey("document.id"), nullable=False)

    document = sa.orm.relationship("Document", backref="annotations")

    thread = sa.orm.relationship(
        "Annotation",
        primaryjoin=(sa.orm.foreign(id) == sa.orm.remote(references[0])),
        viewonly=True,
        uselist=True,
    )

    slim = sa.orm.relationship(
        "AnnotationSlim", uselist=False, back_populates="annotation"
    )

    mentions = relationship("Mention", back_populates="annotation")

    notifications = relationship("Notification", back_populates="source_annotation")

    moderation_status: Mapped[ModerationStatus | None]
    """Current moderation status of the annotation.

    None means the annotation is either "approved" before this column was added  or it's a private annotation.
    """

    moderation_log: Mapped[list["ModerationLog"]] = relationship(
        "ModerationLog", back_populates="annotation"
    )

    #: An optional text description of the annotation target.
    target_description = sa.Column(sa.UnicodeText)

    @property
    def uuid(self):
        """
        Return the UUID representation of the annotation's ID.

        Annotation IDs are stored in the DB as a UUID but represented in the app
        and API in a different format. This property returns the UUID version.
        """
        return UUID(types.URLSafeUUID.url_safe_to_hex(self.id))

    @hybrid_property
    def target_uri(self):
        return self._target_uri

    @target_uri.inplace.setter
    def _target_uri_setter(self, value):
        self._target_uri = value
        self._target_uri_normalized = uri.normalize(value)

    @hybrid_property
    def target_uri_normalized(self):
        return self._target_uri_normalized

    @property
    def target(self):
        target = {"source": self.target_uri}

        if self.target_description is not None:
            target["description"] = self.target_description

        if self.target_selectors:
            target["selector"] = self.target_selectors

        return [target]

    @property
    def quote(self) -> str | None:
        """Quote text the annotation is referring to."""
        selectors = self.target[0].get("selector", [])
        quote = next(
            (s for s in selectors if s.get("type") == "TextQuoteSelector"), None
        )
        return quote.get("exact") if quote else None

    @hybrid_property
    def text(self):
        return self._text

    @text.inplace.setter
    def _text_setter(self, value):
        self._text = value
        # N.B. We MUST take care here of appropriately escaping the user
        # input. Code elsewhere will assume that the content of the
        # `text_rendered` field is safe for printing without further escaping.
        #
        # `markdown.render` does the hard work for now.
        self._text_rendered = markdown_render.render(value)

    @hybrid_property
    def text_rendered(self):
        return self._text_rendered

    @property
    def thread_ids(self):
        return [thread_annotation.id for thread_annotation in self.thread]

    @property
    def is_reply(self):
        return bool(self.references)

    @property
    def parent_id(self):
        """
        Return the ID of the annotation that this annotation is a reply to.

        Return None if this annotation is not a reply.

        """
        if not self.references:
            return None

        return self.references[-1]

    @property
    def thread_root_id(self):
        """
        Return the ID of the root annotation of this annotation's thread.

        Return the ID of the root annotation of the thread to which this
        annotation belongs. May be this annotation's own ID if it is the root
        annotation of its thread.

        """
        if self.references:
            return self.references[0]
        return self.id

    @property
    def authority(self):
        """
        Return the authority of the user and group this annotation belongs to.

        For example, returns "hypothes.is" for Hypothesis first-party
        annotations, or "elifesciences.org" for eLife third-party annotations.

        If this annotation doesn't have a userid (which is possible for
        annotations that haven't been saved to the DB yet) then return None.

        :raises ValueError: if the annotation's userid is invalid

        """
        if self.userid is None:
            return None
        return split_user(self.userid)["domain"]

    @property
    def is_hidden(self) -> bool:
        """Check if this annotation id is hidden."""
        return bool(
            self.moderation_status
            and self.moderation_status != ModerationStatus.APPROVED
        )

    def __repr__(self):
        return f"<Annotation {self.id}>"

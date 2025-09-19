import datetime
import enum
import re
from collections import namedtuple

import slugify
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from h import pubid
from h.db import Base, mixins
from h.models import helpers
from h.models.user import User
from h.util.group import split_groupid

GROUP_NAME_MIN_LENGTH = 3
GROUP_NAME_MAX_LENGTH = 25
GROUP_DESCRIPTION_MAX_LENGTH = 250
AUTHORITY_PROVIDED_ID_PATTERN = r"^[a-zA-Z0-9._\-+!~*()']+$"
AUTHORITY_PROVIDED_ID_MAX_LENGTH = 1024


class JoinableBy(enum.Enum):
    authority = "authority"


class ReadableBy(enum.Enum):
    members = "members"
    world = "world"


class WriteableBy(enum.Enum):
    authority = "authority"
    members = "members"


class GroupMembershipRoles(enum.StrEnum):
    """The valid role strings that're allowed in the GroupMembership.roles column."""

    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"


class GroupMembership(Base):
    __tablename__ = "user_group"

    __table_args__ = (sa.UniqueConstraint("user_id", "group_id"),)

    id = sa.Column("id", sa.Integer, autoincrement=True, primary_key=True)

    user_id = sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="memberships", lazy="selectin")

    group_id = sa.Column(
        "group_id",
        sa.Integer,
        sa.ForeignKey("group.id", ondelete="cascade"),
        nullable=False,
        index=True,
    )
    group = relationship("Group", back_populates="memberships", lazy="selectin")

    roles = sa.Column(
        JSONB,
        sa.CheckConstraint(
            " OR ".join(
                f"""(roles = '["{role}"]'::jsonb)"""
                for role in ["member", "moderator", "admin", "owner"]
            ),
            name="validate_role_strings",
        ),
        server_default=sa.text("""'["member"]'::jsonb"""),
        nullable=False,
    )

    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow, index=True)

    updated = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        index=True,
    )

    def __repr__(self):
        return helpers.repr_(
            self,
            ["id", "user_id", "group_id", "roles"],
        )


class Group(Base, mixins.Timestamps):
    __tablename__ = "group"

    __table_args__ = (
        # Add a composite index of the (authority, authority_provided_id)
        # columns. Also impose uniqueness such that no two records may share
        # the same (authority, authority_provided_id) composite
        #
        # See:
        #
        # * http://docs.sqlalchemy.org/en/latest/core/constraints.html#indexes
        sa.Index(
            "ix__group__groupid", "authority", "authority_provided_id", unique=True
        ),
    )

    id: Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)
    # We don't expose the integer PK to the world, so we generate a short
    # random string to use as the publicly visible ID.
    pubid: Mapped[str] = mapped_column(sa.Text(), default=pubid.generate, unique=True)
    authority: Mapped[str] = mapped_column(sa.UnicodeText())
    name = sa.Column(sa.UnicodeText(), nullable=False, index=True)

    creator_id = sa.Column(sa.Integer, sa.ForeignKey("user.id"))
    creator = sa.orm.relationship("User")

    description = sa.Column(sa.UnicodeText())

    #: Enforce scope match for annotations in this group.
    #: For groups with 1-n scopes, only allow annotations for target
    #: documents whose URIs match one of the group's scopes.
    #: When disabled, annotations should be allowed web-wide.
    #: This setting has no effect if the group does not have any scopes.
    #: Enforcement is the responsibility of services (i.e. the model
    #: layer does not enforce scope compliance).
    enforce_scope = sa.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        server_default=sa.sql.expression.true(),
    )

    #: Allow authorities to define their own unique identifier for a group
    #: (versus the pubid). This identifier is owned by the authority/client
    #: versus ``pubid``, which is owned and controlled by the service.
    authority_provided_id = sa.Column(sa.UnicodeText(), nullable=True, index=True)

    #: Which type of user is allowed to join this group, possible values are:
    #: authority, None
    joinable_by: Mapped[JoinableBy] = mapped_column(
        sa.Enum(JoinableBy, name="group_joinable_by"), nullable=True
    )

    #: Which type of user is allowed to read annotations in this group,
    #: possible values are: authority, members, world
    readable_by: Mapped[ReadableBy | None] = mapped_column(
        sa.Enum(ReadableBy, name="group_readable_by"), nullable=True, index=True
    )

    #: Which type of user is allowed to write to this group, possible values
    #: are: authority, members
    writeable_by: Mapped[WriteableBy | None] = mapped_column(
        sa.Enum(WriteableBy, name="group_writeable_by"), nullable=True
    )

    pre_moderated: Mapped[bool | None] = mapped_column()

    #: A custom Reply-To email address to be used for emails sent from this
    #: group, for example: 'My Group Moderators <mygroup@example.com>'.
    #:
    #: This is used for example as the Reply-To address when the group's
    #: moderators approve or decline an annotation in the group and we send
    #: a notification email to the annotation's author.
    reply_to = sa.Column(sa.UnicodeText(), nullable=True)

    #: A custom name component to be used in the `From` headers of emails sent
    #: from this group, for example: "My Group".
    #:
    #: This does not affect the `From` email address of the group, only the
    #: name part. The email `From` header will be:
    #: `My Group <default_sender@example.com>`
    #: (where default_sender@example.com is the app's default sender address).
    #:
    #: This is used for example in the From address when the group's
    #: moderators approve or decline an annotation in the group and we send
    #: a notification email to the annotation's author.
    email_from_name = sa.Column(sa.UnicodeText(), nullable=True)

    @property
    def groupid(self):
        if self.authority_provided_id is None:
            return None
        return f"group:{self.authority_provided_id}@{self.authority}"

    @groupid.setter
    def groupid(self, value):
        """
        Deconstruct a formatted ``groupid`` and set its constituent properties on the instance.

        If ``groupid`` is set to None, set ``authority_provided_id`` to None
        but leave authority untouched—this allows a caller to nullify the
        ``authority_provided_id`` field.

        :raises ValueError: if ``groupid`` is an invalid format
        """
        if value is None:
            self.authority_provided_id = None
        else:
            groupid_parts = split_groupid(value)
            self.authority_provided_id = groupid_parts["authority_provided_id"]
            self.authority = groupid_parts["authority"]

    memberships = sa.orm.relationship("GroupMembership", back_populates="group")

    @property
    def members(self) -> tuple[User, ...]:
        """
        Return a tuple of this group's members.

        This is a convenience property for when you want to access a group's
        members (User objects) rather than its memberships (GroupMembership
        objects).

        This is not an SQLAlchemy relationship! SQLAlchemy emits a warning if
        you try to have both Group.memberships and a Group.members
        relationships at the same time because it can result in reads returning
        conflicting data and in writes causing integrity errors or unexpected
        inserts or deletes. See:

        https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

        Since this is just a normal Python property setting or mutating it
        (e.g. `group.members = [...]` or `group.members.append(...)`) wouldn't
        be registered with SQLAlchemy and the changes wouldn't be saved to the
        DB. So this is a read-only property that returns an immutable tuple.
        """
        return tuple(membership.user for membership in self.memberships)

    scopes = sa.orm.relationship(
        "GroupScope", backref="group", cascade="all, delete-orphan"
    )

    organization_id = sa.Column(
        sa.Integer, sa.ForeignKey("organization.id"), nullable=True
    )
    organization = sa.orm.relationship("Organization")

    @sa.orm.validates("name")
    def validate_name(self, _key, name):
        if not GROUP_NAME_MIN_LENGTH <= len(name) <= GROUP_NAME_MAX_LENGTH:
            raise ValueError(  # noqa: TRY003
                f"name must be between {GROUP_NAME_MIN_LENGTH} and {GROUP_NAME_MAX_LENGTH} characters long"  # noqa: EM102
            )
        return name

    @sa.orm.validates("authority_provided_id")
    def validate_authority_provided_id(self, _key, authority_provided_id):
        if not authority_provided_id:
            return None

        if not re.match(AUTHORITY_PROVIDED_ID_PATTERN, authority_provided_id):
            raise ValueError(  # noqa: TRY003
                "authority_provided_id must only contain characters allowed"  # noqa: EM101
                r" in encoded URIs: [a-zA-Z0-9._\-+!~*()']"
            )

        if len(authority_provided_id) > AUTHORITY_PROVIDED_ID_MAX_LENGTH:
            raise ValueError(  # noqa: TRY003
                f"authority_provided_id must be {AUTHORITY_PROVIDED_ID_MAX_LENGTH} characters or fewer"  # noqa: EM102
                " characters long"
            )

        return authority_provided_id

    @property
    def slug(self):
        """Get a version of this group's name suitable for use in a URL."""
        return slugify.slugify(self.name)

    @property
    def type(self):
        """
        Get the "type" of this group, e.g. "open" or "private".

        :rtype: string
        :raises ValueError: if the type of the group isn't recognized

        """
        self_type_flags = TypeFlags(
            joinable_by=self.joinable_by,
            readable_by=self.readable_by,
            writeable_by=self.writeable_by,
        )

        for type_, type_flags in GROUP_TYPE_FLAGS.items():
            if self_type_flags == type_flags:
                return type_

        raise ValueError(  # noqa: TRY003
            "This group doesn't seem to match any known type of group. "  # noqa: EM101
            "This shouldn't be in the database!"
        )

    @type.setter
    def type(self, value):
        try:
            new_type_flags = GROUP_TYPE_FLAGS[value]
        except KeyError as err:
            raise ValueError from err

        for index, flag in enumerate(new_type_flags._fields):
            setattr(self, flag, new_type_flags[index])

    @property
    def is_public(self):
        return self.readable_by == ReadableBy.world

    def __repr__(self):
        return helpers.repr_(self, ["id"])


TypeFlags = namedtuple("TypeFlags", "joinable_by readable_by writeable_by")  # noqa: PYI024

GROUP_TYPE_FLAGS = {
    "open": TypeFlags(
        joinable_by=None,
        readable_by=ReadableBy.world,
        writeable_by=WriteableBy.authority,
    ),
    "private": TypeFlags(
        joinable_by=JoinableBy.authority,
        readable_by=ReadableBy.members,
        writeable_by=WriteableBy.members,
    ),
    "restricted": TypeFlags(
        joinable_by=None, readable_by=ReadableBy.world, writeable_by=WriteableBy.members
    ),
}

import datetime
import re
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from h.db import Base
from h.exceptions import InvalidUserId
from h.util.user import format_userid, split_user

if TYPE_CHECKING:
    from models.group import Group


USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = "(?i)^[A-Z0-9._]+$"
EMAIL_MAX_LENGTH = 100
DISPLAY_NAME_MAX_LENGTH = 30


def _normalise_username(username):
    # We normalize usernames by dots and case in order to discourage attempts
    # at impersonation.
    return sa.func.lower(sa.func.replace(username, sa.text("'.'"), sa.text("''")))


class UsernameComparator(
    Comparator
):  # pylint: disable=abstract-method,too-many-ancestors
    """
    Custom comparator for :py:attr:`~h.models.user.User.username`.

    This ensures that all lookups against the username property, such as

        session.query(User).filter_by(username='juanwood')

    use the normalised username for the lookup and appropriately normalise the
    RHS of the query. This means that a query like the one above will
    correctly find a user with a username of "Juan.Wood", for example.
    """

    def operate(self, op, other, **kwargs):  # pylint: disable=arguments-differ
        return op(
            _normalise_username(self.__clause_element__()),
            _normalise_username(other),
            **kwargs,
        )

    def in_(self, other):
        # Normalize the RHS usernames in python
        usernames = [username.lower().replace(".", "") for username in other]
        # And compare them to the normalized LHS in postgres
        return _normalise_username(self.__clause_element__()).in_(usernames)


class UserIDComparator(
    Comparator
):  # pylint: disable=abstract-method,too-many-ancestors
    """
    Custom comparator for :py:attr:`~h.models.user.User.userid`.

    A user's userid is a compound property which depends on their username
    and their authority. A naive comparator for this property would generate
    SQL like the following:

        ... WHERE 'acct:' || username || '@' || authority = ...

    This would be slow, due to the lack of an index on the LHS expression.
    While we could add a functional index on this expression, we can also take
    advantage of the existing index on (normalised_username, authority), which
    is what this comparator does.

    A query such as

        session.query(User).filter_by(userid='acct:luis.silva@example.com')

    will instead generate

        WHERE
            (lower(replace(username,     '.', '')), authority    ) =
            (lower(replace('luis.silva', '.', '')), 'example.com')
    """

    def __init__(self, username, authority):
        super().__init__(sa.tuple_(_normalise_username(username), authority))

    def __eq__(self, other):
        """
        Compare the userid for equality with `other`.

        `other` can be anything plausibly on the RHS of a comparison, which
        can include other SQL clause elements or expressions, as in

            User.userid == sa.tuple_(User.username, Group.authority)

        or literals, as in

            User.userid == 'acct:miruna@example.com'

        We treat the literal case specially, and split the string into
        username and authority ourselves. If the string is not a well-formed
        userid, the comparison will always return False.
        """
        if isinstance(other, str):
            try:
                val = split_user(other)
            except InvalidUserId:
                # The value being compared isn't a valid userid
                return False

            other = sa.tuple_(_normalise_username(val["username"]), val["domain"])

        return self.expression == other

    def in_(self, userids):  # pylint: disable=arguments-renamed
        others = []
        for userid in userids:
            try:
                val = split_user(userid)
            except InvalidUserId:
                continue

            other = sa.tuple_(_normalise_username(val["username"]), val["domain"])
            others.append(other)

        if not others:
            return False

        return self.expression.in_(others)


class User(Base):
    __tablename__ = "user"

    @declared_attr
    def __table_args__(cls):  # pylint:disable=no-self-argument
        return (
            # (email, authority) must be unique
            sa.UniqueConstraint("email", "authority"),
            # (normalised username, authority) must be unique. This index is
            # also critical for making user lookups fast.
            sa.Index(
                "ix__user__userid",
                _normalise_username(cls.username),
                cls.authority,
                unique=True,
            ),
            # Optimize lookup of shadowbanned users.
            sa.Index(
                "ix__user__nipsa", cls.nipsa, postgresql_where=cls.nipsa.is_(True)
            ),
            sa.Index("ix__user__email", sa.func.lower(cls.email)),
        )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    #: Username as chosen by the user on registration
    _username = sa.Column("username", sa.UnicodeText(), nullable=False)

    #: The "authority" for this user. This represents the "namespace" in which
    #: this user lives. By default, all users are created in the namespace
    #: corresponding to `request.domain`, but this can be overridden with the
    #: `h.authority` setting.
    authority = sa.Column("authority", sa.UnicodeText(), nullable=False)

    #: The display name which will be used when rendering an annotation.
    display_name = sa.Column(sa.UnicodeText())

    #: A short user description/bio
    description = sa.Column(sa.UnicodeText())

    #: A free-form column to allow the user to say where they are
    location = sa.Column(sa.UnicodeText())

    #: The user's URI/link on the web
    uri = sa.Column(sa.UnicodeText())

    #: The user's ORCID ID
    orcid = sa.Column(sa.UnicodeText())

    #: Is this user an admin member?
    admin = sa.Column(
        sa.Boolean,
        default=False,
        nullable=False,
        server_default=sa.sql.expression.false(),
    )

    #: Is this user a staff member?
    staff = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    #: Is this user flagged as "Not (Suitable) In Public Site Areas" (AKA
    #: NIPSA). This flag is used to shadow-ban a user so their annotations
    #: don't appear to anyone but themselves.
    nipsa = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    sidebar_tutorial_dismissed = sa.Column(
        sa.Boolean, default=False, server_default=(sa.sql.expression.false())
    )

    #: A timestamp representing the last time the user accepted the privacy policy.
    #: A NULL value in this column indicates the user has never accepted a privacy policy.
    privacy_accepted = sa.Column(sa.DateTime, nullable=True)

    # Has the user opted-in for news etc.
    comms_opt_in = sa.Column(sa.Boolean, nullable=True)

    identities = sa.orm.relationship(
        "UserIdentity", backref="user", cascade="all, delete-orphan"
    )

    @hybrid_property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @username.comparator
    def username(cls):  # pylint:disable=no-self-argument
        return UsernameComparator(cls._username)

    @hybrid_property
    def userid(self):
        return format_userid(self.username, self.authority)

    @userid.comparator
    def userid(cls):  # pylint: disable=no-self-argument
        return UserIDComparator(cls.username, cls.authority)

    email = sa.Column(sa.UnicodeText())

    last_login_date = sa.Column(sa.TIMESTAMP(timezone=False), nullable=True)
    registered_date = sa.Column(
        sa.TIMESTAMP(timezone=False),
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),  # pylint:disable=not-callable
        nullable=False,
    )
    activation_date = sa.Column(sa.TIMESTAMP(timezone=False), nullable=True)

    # Activation foreign key
    activation_id = sa.Column(sa.Integer, sa.ForeignKey("activation.id"))
    activation = sa.orm.relationship("Activation", backref="user")

    @property
    def is_activated(self):
        if self.activation_id is None:
            return True

        return False

    def activate(self):
        """Activate the user by deleting any activation they have."""
        session = sa.orm.object_session(self)

        self.activation_date = datetime.datetime.utcnow()
        session.delete(self.activation)

    #: Hashed password
    password = sa.Column(sa.UnicodeText(), nullable=True)
    #: Last password update
    password_updated = sa.Column(sa.DateTime(), nullable=True)

    #: Password salt
    #:
    #: N.B. This field is DEPRECATED. The password context we use already
    #: manages the generation of a random salt when hashing a password and we
    #: don't need a separate salt column. This remains for "legacy" passwords
    #: which were, sadly, double-salted. As users log in, we are slowly
    #: upgrading their passwords and setting this column to None.
    salt = sa.Column(sa.UnicodeText(), nullable=True)

    #: Has this user been marked for deletion?
    deleted = sa.Column(
        sa.Boolean,
        default=False,
        nullable=False,
        server_default=sa.sql.expression.false(),
    )

    tokens = sa.orm.relationship("Token", back_populates="user")

    memberships = sa.orm.relationship("GroupMembership", back_populates="user")

    @property
    def groups(self) -> tuple["Group", ...]:
        """
        Return a tuple of this user's groups.

        This is a convenience property for when you want to access a user's
        groups (Group objects) rather than its memberships (GroupMembership
        objects).

        This is not an SQLAlchemy relationship! SQLAlchemy emits a warning if
        you try to have both User.memberships and a User.groups relationships
        at the same time because it can result in reads returning conflicting
        data and in writes causing integrity errors or unexpected inserts or
        deletes. See:

        https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html#combining-association-object-with-many-to-many-access-patterns

        Since this is just a normal Python property setting or mutating it
        (e.g. `user.groups = [...]` or `user.groups.append(...)`) wouldn't
        be registered with SQLAlchemy and the changes wouldn't be saved to the
        DB. So this is a read-only property that returns an immutable tuple.
        """
        return tuple(membership.group for membership in self.memberships)

    @sa.orm.validates("email")
    def validate_email(self, _key, email):
        if email is None:
            return email

        if len(email) > EMAIL_MAX_LENGTH:
            raise ValueError(
                f"email must be less than {EMAIL_MAX_LENGTH} characters long"
            )
        return email

    @sa.orm.validates("_username")
    def validate_username(self, _key, username):
        if not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
            raise ValueError(
                f"username must be between {USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} "
                "characters long"
            )

        if not re.match(USERNAME_PATTERN, username):
            raise ValueError(
                "username must have only letters, numbers, periods, and underscores."
            )

        return username

    @classmethod
    def get_by_email(cls, session, email, authority):
        """Fetch a user by email address."""
        if email is None:
            return None

        return (
            session.query(cls)
            .filter(
                sa.func.lower(cls.email) == email.lower(), cls.authority == authority
            )
            .first()
        )

    @classmethod
    def get_by_activation(cls, session, activation):
        """Fetch a user by activation instance."""
        user = session.query(cls).filter(cls.activation_id == activation.id).first()

        return user

    @classmethod
    def get_by_username(cls, session, username, authority):
        """Fetch a user by username."""
        return (
            session.query(cls)
            .filter(cls.username == username, cls.authority == authority)
            .first()
        )

    def __repr__(self):
        return f"<User: {self.username}>"

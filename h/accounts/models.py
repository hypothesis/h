# -*- coding: utf-8 -*-
import datetime
import hashlib
import random
import re
import string

import cryptacular.bcrypt
import sqlalchemy as sa
from sqlalchemy.ext.hybrid import hybrid_property

from h.db import Base
from h._compat import text_type

CRYPT = cryptacular.bcrypt.BCRYPTPasswordManager()
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = '(?i)^[A-Z0-9._]+$'
EMAIL_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 2


def _generate_random_string(length=12):
    """Generate a random ascii string of the requested length."""
    msg = hashlib.sha256()
    word = ''
    for _ in range(length):
        word += random.choice(string.ascii_letters)
    msg.update(word.encode('ascii'))
    return text_type(msg.hexdigest()[:length])


class Activation(Base):

    """
    Handles activations for users.

    The code should be a random hash that is valid only once.
    After the hash is used to access the site, it'll be removed.
    """

    __tablename__ = 'activation'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # A random hash that is valid only once.
    code = sa.Column(sa.UnicodeText(),
                     nullable=False,
                     unique=True,
                     default=_generate_random_string)

    @classmethod
    def get_by_code(cls, session, code):
        """Fetch an activation by code."""
        return session.query(cls).filter(cls.code == code).first()


class User(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    #: Normalised user identifier
    uid = sa.Column(sa.UnicodeText(), nullable=False, unique=True)
    #: Username as chosen by the user on registration
    _username = sa.Column('username',
                          sa.UnicodeText(),
                          nullable=False,
                          unique=True)

    #: The "authority" for this user. This represents the "namespace" in which
    #: this user lives. By default, all users are created in the namespace
    #: corresponding to `request.domain`, but this can be overridden with the
    #: `AUTH_DOMAIN` environment variable.
    authority = sa.Column('authority',
                          sa.UnicodeText(),
                          nullable=False)

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
    admin = sa.Column(sa.Boolean,
                      default=False,
                      nullable=False,
                      server_default=sa.sql.expression.false())

    #: Is this user a staff member?
    staff = sa.Column(sa.Boolean,
                      nullable=False,
                      default=False,
                      server_default=sa.sql.expression.false())

    sidebar_tutorial_dismissed = sa.Column(sa.Boolean,
                                           default=False,
                                           server_default=(
                                                sa.sql.expression.false()))

    @hybrid_property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value
        self.uid = _username_to_uid(value)

    @hybrid_property
    def userid(self):
        return u'acct:' + self.username + u'@' + self.authority

    email = sa.Column(sa.UnicodeText(), nullable=False, unique=True)

    last_login_date = sa.Column(sa.TIMESTAMP(timezone=False),
                                default=datetime.datetime.utcnow,
                                server_default=sa.func.now(),
                                nullable=False)
    registered_date = sa.Column(sa.TIMESTAMP(timezone=False),
                                default=datetime.datetime.utcnow,
                                server_default=sa.func.now(),
                                nullable=False)

    # Activation foreign key
    activation_id = sa.Column(sa.Integer, sa.ForeignKey(Activation.id))
    activation = sa.orm.relationship('Activation', backref='user')

    @property
    def is_activated(self):
        if self.activation_id is None:
            return True

        return False

    def activate(self):
        """Activate the user by deleting any activation they have."""
        session = sa.orm.object_session(self)
        session.delete(self.activation)

    # Hashed password
    _password = sa.Column('password', sa.UnicodeText(), nullable=True)
    # Password salt
    salt = sa.Column(sa.UnicodeText(), nullable=True)
    # Last password update
    password_updated = sa.Column(sa.DateTime(), nullable=True)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        if len(value) < PASSWORD_MIN_LENGTH:
            raise ValueError('password must be more than {min} characters '
                             'long'.format(min=PASSWORD_MIN_LENGTH))
        self.salt = _generate_random_string(24)
        self._password = text_type(CRYPT.encode(value + self.salt))
        self.password_updated = datetime.datetime.utcnow()

    def check_password(self, password):
        """Check the passed password for this user."""
        if self.password is None or self.salt is None:
            return False
        return CRYPT.check(self.password, password + self.salt)

    @sa.orm.validates('email')
    def validate_email(self, key, email):
        if len(email) > EMAIL_MAX_LENGTH:
            raise ValueError('email must be less than {max} characters '
                             'long'.format(max=EMAIL_MAX_LENGTH))
        return email

    @sa.orm.validates('_username')
    def validate_username(self, key, username):
        if not USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH:
            raise ValueError('username must be between {min} and {max} '
                             'characters long'.format(
                                 min=USERNAME_MIN_LENGTH,
                                 max=USERNAME_MAX_LENGTH))

        if not re.match(USERNAME_PATTERN, username):
            raise ValueError('username must contain only letters, numbers, '
                             'periods, and underscores.')

        return username

    @classmethod
    def get_by_email(cls, session, email):
        """Fetch a user by email address."""
        return session.query(cls).filter(
            sa.func.lower(cls.email) == email.lower()
        ).first()

    @classmethod
    def get_by_activation(cls, session, activation):
        """Fetch a user by activation instance."""
        user = session.query(cls).filter(
            cls.activation_id == activation.id
        ).first()

        return user

    @classmethod
    def get_by_username(cls, session, username):
        """Fetch a user by username."""
        uid = _username_to_uid(username)
        return session.query(cls).filter(cls.uid == uid).first()

    def __repr__(self):
        return '<User: %s>' % self.username


def _username_to_uid(username):
    # We normalize usernames by dots and case in order to discourage attempts
    # at impersonation.
    return username.replace('.', '').lower()

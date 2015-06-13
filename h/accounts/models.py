# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
import hashlib
import random
import re
import string

import cryptacular.bcrypt
from hem.db import get_session
from hem.interfaces import IDBSession
from pyramid_basemodel import Base
from pyramid_basemodel import Session
from pyramid.compat import text_type
import sqlalchemy as sa
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property


CRYPT = cryptacular.bcrypt.BCRYPTPasswordManager()


def _generate_random_string(length=12):
    """Generate a random ascii string of the requested length."""
    m = hashlib.sha256()
    word = ''
    for i in range(length):
        word += random.choice(string.ascii_letters)
    m.update(word.encode('ascii'))
    return text_type(m.hexdigest()[:length])


class Activation(Base):

    """
    Handles activations/password reset items for users.

    The code should be a random hash that is valid only once.
    After the hash is used to access the site, it'll be removed.
    """

    __tablename__ = 'activation'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # A random hash that is valid only once.
    code = sa.Column(sa.Unicode(30),
                     nullable=False,
                     unique=True,
                     default=_generate_random_string)

    # FIXME: remove these unused columns
    created_by = sa.Column(sa.Unicode(30), nullable=False, default=u'web')
    valid_until = sa.Column(sa.DateTime,
                            nullable=False,
                            default=datetime.utcnow() + timedelta(days=3))

    @classmethod
    def get_by_code(cls, request, code):
        """Fetch an activation by code."""
        session = get_session(request)
        return session.query(cls).filter(cls.code == code).first()


class User(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # Normalised user identifier
    uid = sa.Column(sa.Unicode(30), nullable=False, unique=True)
    # Username as chosen by the user on registration
    _username = sa.Column('username',
                          sa.Unicode(30),
                          nullable=False,
                          unique=True)

    # Not In Public Site Areas flag
    nipsa = sa.Column(sa.BOOLEAN,
                      default=False,
                      server_default=sa.sql.expression.false(),
                      nullable=False)

    def _get_username(self):
        return self._username

    def _set_username(self, value):
        self._username = value
        self.uid = _username_to_uid(value)

    @declared_attr
    def username(self):
        return sa.orm.synonym('_username',
                              descriptor=property(self._get_username,
                                                  self._set_username))

    email = sa.Column(sa.Unicode(100), nullable=False, unique=True)
    status = sa.Column(sa.Integer())

    last_login_date = sa.Column(sa.TIMESTAMP(timezone=False),
                                default=sa.func.now(),
                                server_default=sa.func.now(),
                                nullable=False)
    registered_date = sa.Column(sa.TIMESTAMP(timezone=False),
                                default=sa.sql.func.now(),
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

    # Hashed password
    _password = sa.Column('password', sa.Unicode(256), nullable=False)
    # Password salt
    salt = sa.Column(sa.Unicode(256), nullable=False)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._set_password(value)

    def _get_password(self):
        return self._password

    def _set_password(self, raw_password):
        self._password = self._hash_password(raw_password)

    def _hash_password(self, password):
        if not self.salt:
            self.salt = _generate_random_string(24)

        return unicode(CRYPT.encode(password + self.salt))

    @classmethod
    def generate_random_password(cls, chars=12):
        """Generate a random string of fixed length."""
        return _generate_random_string(chars)

    @classmethod
    def get_by_email(cls, request, email):
        """Fetch a user by email address."""
        session = get_session(request)

        return session.query(cls).filter(
            sa.func.lower(cls.email) == email.lower()
        ).first()

    @classmethod
    def get_by_email_password(cls, request, email, password):
        """Fetch a user by email address and validate their password."""
        user = cls.get_by_email(request, email)

        if user:
            valid = cls.validate_user(user, password)

            if valid:
                return user

    @classmethod
    def get_by_activation(cls, request, activation):
        """Fetch a user by activation instance."""
        session = get_session(request)

        user = session.query(cls).filter(
            cls.activation_id == activation.id
        ).first()

        return user

    @classmethod
    def get_user(cls, request, username, password):
        """Fetch a user by username and validate their password."""
        user = cls.get_by_username(request, username)

        valid = cls.validate_user(user, password)

        if valid:
            return user

    @classmethod
    def validate_user(cls, user, password):
        """Validate the passed password for the specified user."""
        if not user:
            return None

        if user.password is None:
            valid = False
        else:
            valid = CRYPT.check(user.password, password + user.salt)

        return valid

    @classmethod
    def get_by_id(cls, request, userid):
        """
        Fetch a user by integer id or by full `userid`.

        If `userid` is a string of the form "acct:name@domain.tld" and
        "domain.tld" is the app's current domain, then fetch the user with
        username "name". Otherwise, lookup the user with integer primary key
        `userid`.
        """
        match = re.match(r'acct:([^@]+)@{}'.format(request.domain), userid)
        if match:
            return cls.get_by_username(request, match.group(1))
        session = get_session(request)
        return session.query(cls).filter(cls.id == userid).first()

    @classmethod
    def get_by_username(cls, request, username):
        """Fetch a user by username."""
        session = get_session(request)

        uid = _username_to_uid(username)
        return session.query(cls).filter(cls.uid == uid).first()

    @classmethod
    def get_by_username_or_email(cls, request, username, email):
        session = get_session(request)

        uid = _username_to_uid(username)
        return session.query(cls).filter(
            or_(
                cls.uid == uid,
                cls.email == email
            )
        ).first()

    # TODO: remove all this status bitfield stuff
    @property
    def email_confirmed(self):
        return bool((self.status or 0) & 0b001)

    @email_confirmed.setter
    def email_confirmed(self, value):
        if value:
            self.status = (self.status or 0) | 0b001
        else:
            self.status = (self.status or 0) & ~0b001

    @property
    def optout(self):
        return bool((self.status or 0) & 0b010)

    @optout.setter
    def optout(self, value):
        if value:
            self.status = (self.status or 0) | 0b010
        else:
            self.status = (self.status or 0) & ~0b010

    @property
    def subscriptions(self):
        return bool((self.status or 0) & 0b100)

    @subscriptions.setter
    def subscriptions(self, value):
        if value:
            self.status = (self.status or 0) | 0b100
        else:
            self.status = (self.status or 0) & ~0b100

    @property
    def invited(self):
        return bool((self.status or 0) & 0b1000)

    @invited.setter
    def invited(self, value):
        if value:
            self.status = (self.status or 0) | 0b1000
        else:
            self.status = (self.status or 0) & ~0b1000

    def __repr__(self):
        return '<User: %s>' % self.username


def _username_to_uid(username):
    # We normalise usernames by dots and case in order to discourage attempts
    # at impersonation.
    return username.replace('.', '').lower()


def includeme(config):
    registry = config.registry

    if not registry.queryUtility(IDBSession):
        registry.registerUtility(Session, IDBSession)

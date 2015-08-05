# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
import hashlib
import random
import re
import string

import cryptacular.bcrypt
from pyramid.compat import text_type
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import expression

from h.db import Base
from h import util

CRYPT = cryptacular.bcrypt.BCRYPTPasswordManager()


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
    def get_by_code(cls, code):
        """Fetch an activation by code."""
        return cls.query.filter(cls.code == code).first()


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

    admin = sa.Column(sa.Boolean,
                      default=False,
                      nullable=False,
                      server_default=sa.sql.expression.false())

    # Is this user a staff member?
    staff = sa.Column(sa.Boolean,
                      nullable=False,
                      default=False,
                      server_default=sa.sql.expression.false())

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
    def get_by_email(cls, email):
        """Fetch a user by email address."""
        return cls.query.filter(
            sa.func.lower(cls.email) == email.lower()
        ).first()

    @classmethod
    def get_by_activation(cls, activation):
        """Fetch a user by activation instance."""
        user = cls.query.filter(
            cls.activation_id == activation.id
        ).first()

        return user

    @classmethod
    def get_user(cls, username, password):
        """Fetch a user by username and validate their password."""
        user = cls.get_by_username(username)

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
    def get_by_id(cls, userid):
        """Return the user with the given ID, or None.

        :param userid: A userid unicode string, example:
            u'acct:kim@hypothes.is'
        :type userid: unicode

        :rtype: h.accounts.models.User or None

        """
        parts = util.split_user(userid)
        if parts is None:
            return None
        else:
            username = parts[0]
            return cls.get_by_username(username)

    @classmethod
    def get_by_username(cls, username):
        """Fetch a user by username."""
        uid = _username_to_uid(username)
        return cls.query.filter(cls.uid == uid).first()

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

    @classmethod
    def admins(cls):
        """Return a list of all admin users."""
        return cls.query.filter(
            cls.admin == expression.true()).all()

    @classmethod
    def staff_members(cls):
        """Return a list of all staff members."""
        return cls.query.filter(
            cls.staff == expression.true()).all()

    def __repr__(self):
        return '<User: %s>' % self.username


def _username_to_uid(username):
    # We normalise usernames by dots and case in order to discourage attempts
    # at impersonation.
    return username.replace('.', '').lower()

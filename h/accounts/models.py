# -*- coding: utf-8 -*-
import re

from hem.interfaces import IDBSession
from hem.db import get_session
from horus.interfaces import (
    IActivationClass,
    IUserClass,
    IUIStrings,
)
from horus.models import (
    ActivationMixin,
    GroupMixin,
    UserMixin,
    UserGroupMixin,
)
from horus.strings import UIStringsBase
from pyramid_basemodel import Base, Session
from pyramid.threadlocal import get_current_request
import sqlalchemy as sa
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declared_attr


class Activation(ActivationMixin, Base):
    def __init__(self, *args, **kwargs):
        super(Activation, self).__init__(*args, **kwargs)

        # XXX: Horus currently has a bug where the Activation model isn't
        # flushed before the email is generated, causing the link to be
        # broken (hypothesis/h#1156).
        #
        # Fixed in horus@90f838cef12be249a9e9deb5f38b37151649e801
        request = get_current_request()
        db = get_session(request)
        db.add(self)
        db.flush()


class Group(GroupMixin, Base):
    pass


class User(UserMixin, Base):
    # Database primary key
    _id = sa.Column('id', sa.Integer, autoincrement=True, primary_key=True)

    # Normalised user identifier
    uid = sa.Column(sa.Unicode(30), nullable=False, unique=True)
    # Username as chosen by the user on registration
    _username = sa.Column('username',
                          sa.Unicode(30),
                          nullable=False,
                          unique=True)

    def _get_username(self):
        return self._username

    def _set_username(self, value):
        self._username = value
        self.uid = _username_to_uid(value)

    @declared_attr
    def id(self):
        return sa.orm.synonym('_username',
                              descriptor=property(self._get_username,
                                                  self._set_username))

    @declared_attr
    def username(self):
        return sa.orm.synonym('_username',
                              descriptor=property(self._get_username,
                                                  self._set_username))

    @classmethod
    def get_by_id(cls, request, userid):
        match = re.match(r'acct:([^@]+)@{}'.format(request.domain), userid)
        if match:
            return cls.get_by_username(request, match.group(1))
        else:
            return super(User, cls).get_by_id(request, userid)

    @classmethod
    def get_by_username(cls, request, username):
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


def _username_to_uid(username):
    # We normalise usernames by dots and case in order to discourage attempts
    # at impersonation.
    return username.replace('.', '').lower()


class UserGroup(UserGroupMixin, Base):
    pass


def includeme(config):
    registry = config.registry

    models = [
        (IActivationClass, Activation),
        (IUserClass, User),
        (IUIStrings, UIStringsBase),
        (IDBSession, Session),
    ]

    for iface, imp in models:
        if not registry.queryUtility(iface):
            registry.registerUtility(imp, iface)

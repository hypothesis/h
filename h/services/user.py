# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy

from h.models import Annotation, User
from h import util


class LoginError(Exception):
    pass


class UserNotActivated(LoginError):
    """Tried to log in to an unactivated user account."""


class UserNotKnown(LoginError):
    """User not found while attempting to log in."""


class UserService(object):

    """A service for retrieving and performing common operations on users."""

    def __init__(self, default_authority, session):
        """
        Create a new user service.

        :param default_authority: the default authority for users
        :param session: the SQLAlchemy session object
        """
        self.default_authority = default_authority
        self.session = session

        # Local cache of fetched users.
        self._cache = {}

        # But don't allow the cache to persist after the session is closed.
        @sqlalchemy.event.listens_for(session, 'after_commit')
        @sqlalchemy.event.listens_for(session, 'after_rollback')
        def flush_cache(session):
            self._cache = {}

    def fetch(self, userid_or_username, authority=None):
        """
        Fetch a user by userid or by username and authority.

        Takes *either* a userid *or* a username and authority as arguments.
        For example::

          user_service.fetch('acct:foo@example.com')

        or::

          user_service.fetch('foo', 'example.com')

        :returns: a user instance, if found
        :rtype: h.models.User or None

        """
        if authority is not None:
            username = userid_or_username
        else:
            userid = userid_or_username
            parts = util.user.split_user(userid)
            username = parts['username']
            authority = parts['domain']

        # The cache is keyed by (username, authority) tuples.
        cache_key = (username, authority)

        if cache_key not in self._cache:
            self._cache[cache_key] = (self.session.query(User)
                                      .filter_by(username=username)
                                      .filter_by(authority=authority)
                                      .one_or_none())

        return self._cache[cache_key]

    def login(self, username_or_email, password):
        """
        Attempt to login using *username_or_email* and *password*.

        :returns: A user object if login succeeded, None otherwise.
        :rtype: h.models.User or NoneType
        :raises UserNotActivated: When the user is not activated.
        :raises UserNotKnown: When the user cannot be found in the default
            authority.
        """
        filters = {'authority': self.default_authority}
        if '@' in username_or_email:
            filters['email'] = username_or_email
        else:
            filters['username'] = username_or_email

        user = (self.session.query(User)
                .filter_by(**filters)
                .one_or_none())

        if user is None:
            raise UserNotKnown()

        if not user.is_activated:
            raise UserNotActivated()

        if user.check_password(password):
            return user

        return None


def user_service_factory(context, request):
    """Return a UserService instance for the passed context and request."""
    return UserService(default_authority=request.auth_domain,
                       session=request.db)

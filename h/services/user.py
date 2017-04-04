# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import User
from h.util.db import lru_cache_in_transaction
from h.util.user import split_user

UPDATE_PREFS_ALLOWED_KEYS = set(['show_sidebar_tutorial'])


class UserNotActivated(Exception):
    """Tried to log in to an unactivated user account."""


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

        self._cached_fetch = lru_cache_in_transaction(self.session)(self._fetch)

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
            parts = split_user(userid)
            username = parts['username']
            authority = parts['domain']

        return self._cached_fetch(username, authority)

    def fetch_for_login(self, username_or_email):
        """
        Fetch a user by data provided in the login field.

        This searches for a user by username in the default authority, or by
        email in the default authority if `username_or_email` contains an "@"
        character.

        :returns: A user object if a user was found, None otherwise.
        :rtype: h.models.User or NoneType
        :raises UserNotActivated: When the user is not activated.
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
            return None

        if not user.is_activated:
            raise UserNotActivated()

        return user

    def update_preferences(self, user, **kwargs):
        invalid_keys = set(kwargs.keys()) - UPDATE_PREFS_ALLOWED_KEYS
        if invalid_keys:
            keys = ', '.join(sorted(invalid_keys))
            raise TypeError("settings with keys %s are not allowed" % keys)

        if 'show_sidebar_tutorial' in kwargs:
            user.sidebar_tutorial_dismissed = not kwargs['show_sidebar_tutorial']

    def _fetch(self, username, authority):
        return (self.session.query(User)
                    .filter_by(username=username)
                    .filter_by(authority=authority)
                    .one_or_none())


def user_service_factory(context, request):
    """Return a UserService instance for the passed context and request."""
    return UserService(default_authority=request.authority,
                       session=request.db)

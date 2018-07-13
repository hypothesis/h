# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.i18n import TranslationString as _  # noqa: N813
from h import models


class DuplicateUserError(Exception):
    """Indicates that data violates user uniqueness constraints"""

    def __init__(self, message):
        super(DuplicateUserError, self).__init__(message)


class UserUniqueService(object):

    """
    A service for ensuring that data represents a unique user and will
    not constitute a duplicate user.
    """

    def __init__(self, session, request_authority):
        """
        Create a new user_unique service.

        :param _session: the SQLAlchemy session object
        """
        self._session = session
        self.request_authority = request_authority

    def ensure_unique(self, data, authority=None):
        """
        Ensure the provided `data` would constitute a new, non-duplicate
        user. Check for conflicts in email, username, identity.

        :param data: dictionary of new-user data. Will check `email`, `username`
                     and any `identities` dictionaries provided
        :raises ConflictError: if the data violate any uniqueness constraints
        """
        authority = authority or self.request_authority
        errors = []

        if data.get('email', None) and (
            models.User.get_by_email(self._session, data['email'], authority)
        ):
            errors.append(_('user with email address %s already exists' % data['email']))

        if data.get('username', None) and (
            models.User.get_by_username(self._session, data['username'], authority)
        ):
            errors.append(_('user with username %s already exists' % data['username']))

        if errors:
            raise DuplicateUserError(', '.join(errors))


def user_unique_factory(context, request):
    return UserUniqueService(session=request.db,
                             request_authority=request.authority)

# -*- coding: utf-8 -*-
from h import util
from h.accounts import models


class Error(Exception):

    """Base class for this package's custom exception classes."""

    pass


class NoSuchUserError(Error):

    """Exception raised when asking for a user that doesn't exist."""

    pass


def make_admin(username):
    """Make the given user an admin."""
    user = models.User.get_by_username(username)
    if user:
        user.admin = True
    else:
        raise NoSuchUserError


def make_staff(username):
    """Make the given user a staff member."""
    user = models.User.get_by_username(username)
    if user:
        user.staff = True
    else:
        raise NoSuchUserError


def authenticated_user(request):
    """Return the authenticated user or None.

    :rtype: h.accounts.models.User or None

    """
    if not request.authenticated_userid:
        return None

    try:
        parts = util.split_user(request.authenticated_userid)
    except ValueError:
        return None

    auth_domain = request.registry.settings.get(
        'h.auth_domain', request.domain)

    if parts['domain'] != auth_domain:
        return None

    return models.User.get_by_username(parts['username'])


def includeme(config):
    """A local identity provider."""
    config.add_request_method(
        authenticated_user, name='authenticated_user', reify=True)

    config.include('.schemas')
    config.include('.subscribers')
    config.include('.views')

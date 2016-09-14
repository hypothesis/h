# -*- coding: utf-8 -*-
from itsdangerous import URLSafeTimedSerializer
from pyramid import httpexceptions

from h.security import derive_key


class Error(Exception):

    """Base class for this package's custom exception classes."""

    pass


class JSONError(Error):

    """Exception raised when there's a problem with a request's JSON body.

    This is for pre-validation problems such as no JSON body, body cannot
    be parsed as JSON, or top-level keys missing from the JSON.

    """

    pass


def authenticated_user(request):
    """Return the authenticated user or None.

    :rtype: h.models.User or None

    """
    if request.authenticated_userid is None:
        return None

    user_service = request.find_service(name='user')
    user = user_service.fetch(request.authenticated_userid)

    # If the authenticated user doesn't exist in the db then log them out.
    # This happens when we delete a user account but the user still has a
    # valid session for that account (because we don't invalidate sessions
    # when we delete user accounts).
    #
    # FIXME: switch to authentication ticket based sessions so that we *can*
    # invalidate sessions when deleting users. Throwing a 302 in the middle of
    # an arbitrary request is NOT safe (e.g. POST requests).
    if request.authenticated_userid and not user:
        request.session.invalidate()
        raise httpexceptions.HTTPFound(location=request.url)

    return user


def includeme(config):
    """A local identity provider."""

    # Add a `request.authenticated_user` property.
    #
    # N.B. we use `property=True` and not `reify=True` here because it is
    # important that responsibility for caching user lookups is left to the
    # UserService and not duplicated here.
    #
    # This prevents retried requests (those that raise
    # `transaction.interfaces.TransientError`) gaining access to a stale
    # `User` instance.
    config.add_request_method(authenticated_user, property=True)

    config.register_service_factory('.services.user_service_factory',
                                    name='user')
    config.register_service_factory('.services.user_signup_service_factory',
                                    name='user_signup')

    config.include('.schemas')
    config.include('.subscribers')

    secret = config.registry.settings['secret_key']
    derived = derive_key(secret, b'h.accounts')
    serializer = URLSafeTimedSerializer(derived)
    config.registry.password_reset_serializer = serializer

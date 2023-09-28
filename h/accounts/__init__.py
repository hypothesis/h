from itsdangerous import URLSafeTimedSerializer

from h.security import derive_key


class Error(Exception):
    """Base class for this package's custom exception classes."""


class JSONError(Error):
    """
    Exception raised when there's a problem with a request's JSON body.

    This is for pre-validation problems such as no JSON body, body cannot
    be parsed as JSON, or top-level keys missing from the JSON.

    """


def get_user(request):
    """
    Return the user for the request or None.

    :rtype: h.models.User or None

    """
    if request.authenticated_userid is None:
        return None

    user_service = request.find_service(name="user")
    user = user_service.fetch(request.authenticated_userid)

    return user


def includeme(config):  # pragma: no cover
    # Add a `request.user` property.
    #
    # N.B. we use `property=True` and not `reify=True` here because it is
    # important that responsibility for caching user lookups is left to the
    # UserService and not duplicated here.
    #
    # This prevents requests that are retried by pyramid_retry gaining access
    # to a stale `User` instance.
    config.add_request_method(get_user, name="user", property=True)

    config.include(".schemas")

    secret = config.registry.settings["secret_key"]
    salt = config.registry.settings["secret_salt"]
    derived = derive_key(secret, salt, b"h.accounts")
    serializer = URLSafeTimedSerializer(derived)
    config.registry.password_reset_serializer = serializer

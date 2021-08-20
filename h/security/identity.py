from dataclasses import dataclass

from pyramid.interfaces import IAuthenticationPolicy

from h.models import AuthClient, User


@dataclass
class Identity:
    """
    The identity of the logged in user/client.

    This can include a user if the user is directly logged in, or provided via
    a forwarded user. An `AuthClient` if this is a call is made using a
    pre-shared key, or both.
    """

    user: User = None
    auth_client: AuthClient = None


def get_identity(request):
    """
    Get the identity associated with a request.

    This is a Pyramid 2.0 compatibility addition and should be removed when
    we upgrade. This is used as a request method `identity()` to mirror that
    added by Pyramid 2.0.
    """
    return request.registry.queryUtility(IAuthenticationPolicy).identity(request)

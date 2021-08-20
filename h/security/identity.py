from dataclasses import dataclass

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

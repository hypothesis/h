from dataclasses import dataclass

from h.models import AuthClient, User


@dataclass
class Identity:
    user: User = None
    auth_client: AuthClient = None

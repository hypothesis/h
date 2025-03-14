import random
from datetime import datetime, timedelta

import factory

from h import models

from .auth_client import AuthClient
from .base import ModelFactory
from .user import User


def generate_code(_=None):
    """Simulate the way oauthlib generates authz codes."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    rand = random.SystemRandom()
    return "".join(rand.choice(chars) for x in range(30))


class AuthzCode(ModelFactory):
    class Meta:
        model = models.AuthzCode
        sqlalchemy_session_persistence = "flush"

    user = factory.SubFactory(User)
    authclient = factory.SubFactory(AuthClient)
    code = factory.LazyAttribute(generate_code)
    expires = factory.LazyAttribute(
        lambda _: (datetime.utcnow() + timedelta(minutes=10))  # noqa: DTZ003
    )

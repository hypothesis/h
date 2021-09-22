import factory

from h import models

from .base import ModelFactory


class UserIdentity(ModelFactory):
    class Meta:
        model = models.UserIdentity
        sqlalchemy_session_persistence = "flush"

    provider = factory.Sequence(lambda n: f"test_provider_{n}")
    provider_unique_id = factory.Sequence(lambda n: f"test_id_{n}")

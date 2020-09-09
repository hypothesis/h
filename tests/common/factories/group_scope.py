import factory

from h import models

from .base import ModelFactory


class GroupScope(ModelFactory):
    class Meta:
        model = models.GroupScope
        sqlalchemy_session_persistence = "flush"

    scope = factory.Faker("url")
    group = factory.SubFactory("tests.common.factories.OpenGroup")

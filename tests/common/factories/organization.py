import factory

from h import models

from .base import ModelFactory


class Organization(ModelFactory):
    class Meta:
        model = models.Organization
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"Test Organization {n}")
    authority = "example.com"

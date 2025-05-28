import factory

from h import models

from .base import ModelFactory


class GroupMembership(ModelFactory):
    class Meta:
        model = models.GroupMembership
        sqlalchemy_session_persistence = "flush"

    roles = factory.Faker("random_element", elements=models.GroupMembershipRoles)

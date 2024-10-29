import factory
from factory import Faker

from h import models
from h.models.group import JoinableBy, ReadableBy, WriteableBy

from .base import ModelFactory
from .group_scope import GroupScope
from .user import User


class Group(ModelFactory):
    class Meta:
        model = models.Group
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: f"Group {n}")
    authority = "example.com"
    creator = factory.SubFactory(User)
    joinable_by = JoinableBy.authority
    readable_by = ReadableBy.members
    writeable_by = WriteableBy.members
    authority_provided_id = Faker("hexify", text="^" * 30)
    enforce_scope = True

    @factory.post_generation
    def scopes(  # pylint: disable=method-hidden,unused-argument
        self, create, scopes=0, **kwargs
    ):
        if isinstance(scopes, int):
            scopes = [GroupScope(group=self) for _ in range(0, scopes)]

        self.scopes = scopes or []


class OpenGroup(Group):
    name = factory.Sequence(lambda n: f"Open Group {n}")

    joinable_by = None
    readable_by = ReadableBy.world
    writeable_by = WriteableBy.authority


class RestrictedGroup(Group):
    name = factory.Sequence(lambda n: f"Restricted Group {n}")

    joinable_by = None
    readable_by = ReadableBy.world

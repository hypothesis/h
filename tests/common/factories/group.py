import factory

from h import models
from h.models.group import JoinableBy, ReadableBy, WriteableBy

from .base import ModelFactory
from .group_scope import GroupScope
from .user import User


class Group(ModelFactory):
    class Meta:
        model = models.Group
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: "Group {n}".format(n=str(n)))
    authority = "example.com"
    creator = factory.SubFactory(User)
    joinable_by = JoinableBy.AUTHORITY
    readable_by = ReadableBy.MEMBERS
    writeable_by = WriteableBy.MEMBERS
    members = factory.LazyAttribute(lambda obj: [obj.creator])
    enforce_scope = True

    @factory.post_generation
    def scopes(self, create, scopes=0, **kwargs):
        if isinstance(scopes, int):
            scopes = [GroupScope(group=self) for _ in range(0, scopes)]

        self.scopes = scopes or []


class OpenGroup(Group):

    name = factory.Sequence(lambda n: "Open Group {n}".format(n=str(n)))

    joinable_by = None
    readable_by = ReadableBy.WORLD
    writeable_by = WriteableBy.AUTHORITY
    members = []


class RestrictedGroup(Group):
    name = factory.Sequence(lambda n: "Restricted Group {n}".format(n=str(n)))

    joinable_by = None
    readable_by = ReadableBy.WORLD

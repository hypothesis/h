# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models
from h.models.group import JoinableBy, ReadableBy, WriteableBy

from .base import ModelFactory
from .group_scope import GroupScope
from .user import User


class Group(ModelFactory):

    class Meta:
        model = models.Group
        sqlalchemy_session_persistence = 'flush'

    name = factory.Sequence(lambda n: 'Test Group {n}'.format(n=str(n)))
    authority = 'example.com'
    creator = factory.SubFactory(User)
    joinable_by = JoinableBy.authority
    readable_by = ReadableBy.members
    writeable_by = WriteableBy.members
    members = factory.LazyAttribute(lambda obj: [obj.creator])

    @factory.post_generation
    def scopes(self, create, scopes=0, **kwargs):
        if isinstance(scopes, int):
            scopes = [GroupScope(group=self) for _ in range(0, scopes)]

        self.scopes = scopes or []


class OpenGroup(Group):

    name = factory.Sequence(lambda n: 'Test Open Group {n}'.format(n=str(n)))

    joinable_by = None
    readable_by = ReadableBy.world
    writeable_by = WriteableBy.authority
    members = []


class RestrictedGroup(Group):
    name = factory.Sequence(lambda n: 'Test Restricted Group {n}'.format(n=str(n)))

    joinable_by = None
    readable_by = ReadableBy.world

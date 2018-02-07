# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import random

import factory

from h import models

from .base import ModelFactory
from .group import Group


class GroupScope(ModelFactory):
    class Meta:
        model = models.GroupScope

    hostname = factory.Faker('domain_name')

    @factory.post_generation
    def groups(self, create, groups, **kwargs):
        if groups is None:
            groups = random.randint(1, 3)

        if isinstance(groups, int):
            groups = [Group() for _ in range(0, groups)]

        self.groups = groups or []

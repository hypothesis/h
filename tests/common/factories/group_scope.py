# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import ModelFactory
from .group import OpenGroup


class GroupScope(ModelFactory):
    class Meta:
        model = models.GroupScope

    origin = factory.Faker('url')
    group = factory.SubFactory(OpenGroup)

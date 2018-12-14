# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import ModelFactory


class GroupScope(ModelFactory):
    class Meta:
        model = models.GroupScope
        sqlalchemy_session_persistence = "flush"

    origin = factory.Faker("url")
    group = factory.SubFactory("tests.common.factories.OpenGroup")

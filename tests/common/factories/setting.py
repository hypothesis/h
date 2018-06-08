# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import FAKER, ModelFactory


class Setting(ModelFactory):
    class Meta:
        model = models.Setting
        sqlalchemy_session_persistence = "flush"

    key = factory.Sequence(lambda n: "setting_%d" % n)
    value = factory.LazyAttribute(lambda _: FAKER.catch_phrase())

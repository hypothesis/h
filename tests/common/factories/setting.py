# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import FAKER, ModelFactory


class Setting(ModelFactory):

    class Meta:
        model = models.Setting
        force_flush = True

    key = factory.LazyAttribute(lambda _: FAKER.domain_word())
    value = factory.LazyAttribute(lambda _: FAKER.catch_phrase())

# -*- coding: utf-8 -*-

import factory

from h import models

from .base import ModelFactory


class Feature(ModelFactory):
    class Meta:
        model = models.Feature

    name = factory.Sequence(lambda n: "feature_%d" % n)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory
from .user import User


class Flag(ModelFactory):

    class Meta:
        model = models.Flag
        force_flush = True

    user = factory.SubFactory(User)
    annotation = factory.SubFactory(Annotation)

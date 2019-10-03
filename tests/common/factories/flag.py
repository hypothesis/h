# -*- coding: utf-8 -*-

import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory
from .user import User


class Flag(ModelFactory):
    class Meta:
        model = models.Flag
        sqlalchemy_session_persistence = "flush"

    user = factory.SubFactory(User)
    annotation = factory.SubFactory(Annotation)

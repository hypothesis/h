# -*- coding: utf-8 -*-

import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory


class AnnotationModeration(ModelFactory):

    class Meta:
        model = models.AnnotationModeration
        sqlalchemy_session_persistence = 'flush'

    annotation = factory.SubFactory(Annotation)

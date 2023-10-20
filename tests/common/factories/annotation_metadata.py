import factory

from h import models

from .annotation_slim import AnnotationSlim
from .base import ModelFactory


class AnnotationMetadata(ModelFactory):
    class Meta:
        model = models.AnnotationMetadata
        sqlalchemy_session_persistence = "flush"

    annotation_slim = factory.SubFactory(AnnotationSlim)

import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory


class AnnotationMetadata(ModelFactory):
    class Meta:
        model = models.AnnotationMetadata
        sqlalchemy_session_persistence = "flush"

    annotation = factory.SubFactory(Annotation)

import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory


class AnnotationModeration(ModelFactory):
    class Meta:
        model = models.AnnotationModeration
        sqlalchemy_session_persistence = "flush"

    annotation = factory.SubFactory(Annotation)

    @factory.post_generation
    def slim(self, create, extracted, **kwargs):  # pylint:disable=unused-argument
        if self.annotation.slim:
            self.annotation.slim.moderated = True

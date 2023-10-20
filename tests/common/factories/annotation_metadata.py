import factory

from h import models
from tests.common.factories.annotation_slim import AnnotationSlim
from tests.common.factories.base import ModelFactory


class AnnotationMetadata(ModelFactory):
    class Meta:
        model = models.AnnotationMetadata

    annotation_slim = factory.SubFactory(AnnotationSlim)

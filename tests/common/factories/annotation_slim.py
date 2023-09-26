import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory
from .document import Document
from .group import Group
from .user import User


class AnnotationSlim(ModelFactory):
    class Meta:
        model = models.AnnotationSlim

    annotation = factory.SubFactory(Annotation)
    user = factory.SubFactory(User)
    group = factory.SubFactory(Group)
    document = factory.SubFactory(Document)

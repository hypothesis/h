import factory

from h import models

from .base import ModelFactory
from .document import Document
from .group import Group


class Checkpoint(ModelFactory):
    class Meta:
        model = models.Checkpoint
        sqlalchemy_session_persistence = "flush"

    group = factory.SubFactory(Group)
    document = factory.SubFactory(Document)

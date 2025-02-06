import factory

from h import models

from .annotation import Annotation
from .base import ModelFactory
from .user import User


class Mention(ModelFactory):
    class Meta:
        model = models.Mention
        sqlalchemy_session_persistence = "flush"

    annotation = factory.SubFactory(Annotation)
    user = factory.SubFactory(User)
    username = factory.LazyAttribute(lambda obj: obj.user.username)

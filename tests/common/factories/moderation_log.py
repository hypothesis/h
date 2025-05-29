import factory

from h import models
from tests.common.factories.annotation import Annotation
from tests.common.factories.user import User

from .base import ModelFactory


class ModerationLog(ModelFactory):
    class Meta:
        model = models.ModerationLog
        sqlalchemy_session_persistence = "flush"

    annotation = factory.SubFactory(Annotation)
    old_moderation_status = factory.Faker(
        "random_element", elements=models.ModerationStatus
    )
    new_moderation_status = factory.Faker(
        "random_element", elements=models.ModerationStatus
    )
    moderator = factory.SubFactory(User)

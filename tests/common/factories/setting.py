import factory

from h import models

from .base import FAKER, ModelFactory


class Setting(ModelFactory):
    class Meta:
        model = models.Setting
        sqlalchemy_session_persistence = "flush"

    key = factory.Sequence(lambda n: f"setting_{n}")
    value = factory.LazyAttribute(
        lambda _: FAKER.catch_phrase()  # pylint: disable=no-member
    )

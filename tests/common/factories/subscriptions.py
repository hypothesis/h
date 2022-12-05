import factory
from factory import Faker

from h import models
from tests.common.factories.base import FAKER, ModelFactory


class Subscriptions(ModelFactory):
    class Meta:
        model = models.Subscriptions

    uri = factory.LazyAttribute(
        lambda _: (
            "acct:" + FAKER.user_name() + "@example.com"  # pylint:disable=no-member
        )
    )
    type = models.Subscriptions.Type.REPLY.value
    active = Faker("random_element", elements=[True, False])

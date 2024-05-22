from factory import Faker, LazyAttribute

from h import models

from .base import ModelFactory


class UserDeletion(ModelFactory):
    class Meta:
        model = models.UserDeletion
        exclude = ("username", "requesting_username")

    username = Faker("user_name")
    userid = LazyAttribute(lambda o: f"acct:{o.username}@example.com")
    requesting_username = Faker("user_name")
    requested_by = LazyAttribute(lambda o: f"acct:{o.requesting_username}@example.com")
    tag = "factory"
    registered_date = Faker("date_time")
    num_annotations = Faker("random_int")

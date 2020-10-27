from factory import Faker

from h import models

from .base import ModelFactory


class Job(ModelFactory):
    class Meta:
        model = models.Job

    name = "test_job"
    priority = Faker("random_element", elements=[1, 100, 1000, 10000])
    tag = "test_tag"

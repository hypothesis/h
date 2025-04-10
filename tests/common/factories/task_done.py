from factory import LazyFunction, post_generation

from h import models

from .base import ModelFactory


class TaskDone(ModelFactory):
    class Meta:
        model = models.TaskDone

    data = LazyFunction(lambda: None)

    @post_generation
    def expires_at(self, _create, extracted, **_kwargs):
        if extracted:
            self.expires_at = extracted

    @post_generation
    def created(self, _create, extracted, **_kwargs):
        if extracted:
            self.created = extracted

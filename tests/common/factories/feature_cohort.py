from factory import Sequence, post_generation

from h import models

from .base import ModelFactory


class FeatureCohort(ModelFactory):
    class Meta:
        model = models.FeatureCohort

    name = Sequence(lambda n: f"featurecohort_{n}")

    @post_generation
    def members(self, _create, extracted, **_kwargs):
        if extracted:
            self.members.extend(extracted)

    @post_generation
    def features(self, _create, extracted, **_kwargs):
        if extracted:
            self.features.extend(extracted)

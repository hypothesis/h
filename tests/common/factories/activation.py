from h import models

from .base import ModelFactory


class Activation(ModelFactory):
    class Meta:
        model = models.Activation
        sqlalchemy_session_persistence = "flush"

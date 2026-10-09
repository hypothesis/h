from datetime import datetime

import factory

from h import models

from .base import ModelFactory
from .user import User


class UserSurveyResponse(ModelFactory):
    class Meta:
        model = models.UserSurveyResponse
        sqlalchemy_session_persistence = "flush"

    user = factory.SubFactory(User)
    survey = "edu_role"
    response = "instructor"
    responded_at = factory.LazyFunction(datetime.utcnow)

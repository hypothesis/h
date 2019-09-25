# -*- coding: utf-8 -*-

import factory

from h import models

from .base import FAKER, ModelFactory


class AuthClient(ModelFactory):
    class Meta:
        model = models.AuthClient
        sqlalchemy_session_persistence = "flush"

    authority = "example.com"
    redirect_uri = "https://example.com/auth/callback"


class ConfidentialAuthClient(ModelFactory):
    class Meta:
        model = models.AuthClient
        sqlalchemy_session_persistence = "flush"

    authority = "example.com"
    secret = factory.LazyAttribute(lambda _: FAKER.sha256())
    redirect_uri = "https://example.com/auth/callback"

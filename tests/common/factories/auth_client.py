# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models
from h._compat import text_type

from .base import FAKER, ModelFactory


class AuthClient(ModelFactory):

    class Meta:
        model = models.AuthClient
        force_flush = True

    authority = 'example.com'
    secret = factory.LazyAttribute(lambda _: text_type(FAKER.sha256()))
    redirect_uri = 'https://example.com/auth/callback'

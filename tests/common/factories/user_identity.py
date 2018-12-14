# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import ModelFactory


class UserIdentity(ModelFactory):
    class Meta:
        model = models.UserIdentity
        sqlalchemy_session_persistence = "flush"

    provider = factory.Sequence(lambda n: "test_provider_{n}".format(n=str(n)))
    provider_unique_id = factory.Sequence(lambda n: "test_id_{n}".format(n=str(n)))

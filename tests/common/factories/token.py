# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models
from h import security
from h.services.developer_token import PREFIX

from .base import FAKER, ModelFactory


class DeveloperToken(ModelFactory):

    class Meta:
        model = models.Token
        sqlalchemy_session_persistence = 'flush'

    userid = factory.LazyAttribute(lambda _: ('acct:' + FAKER.user_name() + '@example.com'))
    value = factory.LazyAttribute(lambda _: (PREFIX + security.token_urlsafe()))

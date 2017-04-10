# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import FAKER, ModelFactory


class Token(ModelFactory):

    class Meta:
        model = models.Token
        force_flush = True

    userid = factory.LazyAttribute(lambda _: ('acct:' + FAKER.user_name() + '@example.com'))

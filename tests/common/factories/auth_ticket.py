# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
import os
from datetime import datetime, timedelta

import factory

from h import models

from .base import ModelFactory
from .user import User


class AuthTicket(ModelFactory):
    class Meta:
        model = models.AuthTicket

    # Simulate how pyramid_authsanity generates ticket ids
    id = factory.LazyAttribute(
        lambda _: base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
    )
    user = factory.SubFactory(User)
    expires = factory.LazyAttribute(
        lambda _: (datetime.utcnow() + timedelta(minutes=10))
    )

    @factory.lazy_attribute
    def user_userid(self):
        return self.user.userid

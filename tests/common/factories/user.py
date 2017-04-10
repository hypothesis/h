# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .activation import Activation
from .base import ModelFactory


class User(ModelFactory):

    class Meta:
        model = models.User

    class Params:
        inactive = factory.Trait(activation=factory.SubFactory(Activation))

    authority = 'example.com'
    username = factory.Faker('user_name')
    email = factory.Faker('email')
    registered_date = factory.Faker('date_time_this_decade')

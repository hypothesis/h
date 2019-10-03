# -*- coding: utf-8 -*-

import factory

from h import models

from .base import ModelFactory


class Organization(ModelFactory):
    class Meta:
        model = models.Organization
        sqlalchemy_session_persistence = "flush"

    name = factory.Sequence(lambda n: "Test Organization {n}".format(n=str(n)))
    authority = "example.com"

# -*- coding: utf-8 -*-
"""Factory classes for easily generating test objects."""

from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import os
from datetime import (datetime, timedelta)

import factory
import faker

from h import models
from h.models.group import JoinableBy, ReadableBy, WriteableBy

from ..memex import factories as memex_factories


FAKER = faker.Factory.create()
SESSION = None

Annotation = memex_factories.Annotation
Document = memex_factories.Document
DocumentMeta = memex_factories.DocumentMeta
DocumentURI = memex_factories.DocumentURI


def set_session(value):
    global SESSION

    SESSION = value
    memex_factories.SESSION = value


class ModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:  # pylint: disable=no-init, old-style-class
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # We override SQLAlchemyModelFactory's default _create classmethod so
        # that rather than fetching the session from cls._meta (which is
        # created at parse time... ugh) we fetch it from the SESSION global,
        # which is dynamically filled out by the `factories` fixture when
        # used.
        if SESSION is None:
            raise RuntimeError('no session: did you use the factories fixture?')
        obj = model_class(*args, **kwargs)
        SESSION.add(obj)
        if cls._meta.force_flush:
            SESSION.flush()
        return obj


class Activation(ModelFactory):

    class Meta(object):
        model = models.Activation
        force_flush = True


class AuthClient(ModelFactory):

    class Meta(object):
        model = models.AuthClient
        force_flush = True

    authority = 'example.com'
    secret = factory.LazyAttribute(lambda _: unicode(FAKER.sha256()))


class User(ModelFactory):

    """A factory class that generates h.models.User objects."""

    class Meta(object):
        model = models.User

    class Params(object):
        inactive = factory.Trait(
            activation=factory.SubFactory(Activation),
        )

    authority = 'example.com'
    username = factory.Faker('user_name')
    email = factory.Faker('email')
    registered_date = factory.Faker('date_time_this_decade')

    @factory.lazy_attribute
    def uid(self):
        return self.username.replace('.', '').lower()


class Group(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Group
        force_flush = True

    name = factory.Sequence(lambda n:'Test Group {n}'.format(n=str(n)))
    authority = 'example.com'
    creator = factory.SubFactory(User)
    joinable_by = JoinableBy.authority
    readable_by = ReadableBy.members
    writeable_by = WriteableBy.members


class PublisherGroup(Group):

    name = factory.Sequence(lambda n: 'Test Publisher Group {n}'.format(n=str(n)))

    joinable_by = None
    readable_by = ReadableBy.world
    writeable_by = WriteableBy.authority


class AuthTicket(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.AuthTicket

    # Simulate how pyramid_authsanity generates ticket ids
    id = factory.LazyAttribute(lambda _: base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode('ascii'))
    user = factory.SubFactory(User)
    expires = factory.LazyAttribute(lambda _: (datetime.utcnow() + timedelta(minutes=10)))

    @factory.lazy_attribute
    def user_userid(self):
        return self.user.userid


class Token(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Token
        force_flush = True

    userid = factory.LazyAttribute(lambda _: ('acct:' + FAKER.user_name() + '@example.com'))


class Setting(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Setting
        force_flush = True

    key = factory.LazyAttribute(lambda _: FAKER.domain_word())
    value = factory.LazyAttribute(lambda _: FAKER.catch_phrase())

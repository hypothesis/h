# -*- coding: utf-8 -*-
"""Factory classes for easily generating test objects."""

from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import os
from datetime import (datetime, timedelta)
import random

import factory
import faker
from sqlalchemy import orm

from h import models
from memex import models as api_models


FAKER = faker.Factory.create()
SESSION = None


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


class Document(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Document


class DocumentMeta(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.DocumentMeta

    # Trying to add two DocumentMetas with the same claimant and type to the
    # db will crash. We use a sequence instead of something like FAKER.url()
    # for claimant here so that never happens (unless you pass in your own
    # claimant).
    claimant = factory.Sequence(
        lambda n: 'http://example.com/document_' + str(n) + '/')

    type = factory.Iterator([
        'title', 'twitter.url.main_url', 'twitter.title', 'favicon'])
    document = factory.SubFactory(Document)

    @factory.lazy_attribute
    def value(self):
        if self.type == 'twitter.url.main_url':
            return [FAKER.url()]
        elif self.type == 'favicon':
            return [FAKER.image_url()]
        else:
            return [FAKER.bs()]


class DocumentURI(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.DocumentURI

    # Trying to add two DocumentURIs with the same claimant, uri, type and
    # content_type to the db will crash. We use a sequence instead of something
    # like FAKER.url() for claimant here so that never happens (unless you pass
    # in your own claimant).
    claimant = factory.Sequence(
        lambda n: 'http://example.com/document_' + str(n) + '/')

    uri = factory.LazyAttribute(lambda obj: obj.claimant)
    type = factory.Iterator(['rel-alternate', 'rel-canonical', 'highwire-pdf',
                             'dc-doi'])
    content_type = factory.Iterator(['text/html', 'application/pdf',
                                     'text/plain'])
    document = factory.SubFactory(Document)


class Annotation(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Annotation
        force_flush = True  # Always flush the db to generate annotation.id.

    tags = factory.LazyFunction(
        lambda: FAKER.words(nb=random.randint(0, 5)))
    target_uri = factory.Faker('uri')
    text = factory.Faker('paragraph')
    userid = factory.Faker('user_name')

    @factory.lazy_attribute
    def target_selectors(self):  # pylint: disable=no-self-use
        return [
            {
                'endContainer': '/div[1]/article[1]/section[1]/div[1]/div[2]/div[1]',
                'endOffset': 76,
                'startContainer': '/div[1]/article[1]/section[1]/div[1]/div[2]/div[1]',
                'startOffset': 0,
                'type': 'RangeSelector'
            },
            {
                'end': 362,
                'start': 286,
                'type': 'TextPositionSelector'
            },
            {
                'exact': 'If you wish to install Hypothesis on your own site then head over to GitHub.',
                'prefix': ' browser extension.\n            ',
                'suffix': '\n          \n        \n      \n    ',
                'type': 'TextQuoteSelector'
            },
        ]

    @factory.post_generation
    def make_metadata(self, create, extracted, **kwargs):
        """Create associated document metadata for the annotation."""
        # The metadata objects are going to be added to the db, so if we're not
        # using the create strategy then simply don't make any.
        if not create:
            return

        def document_uri_dict():
            """
            Return a randomly generated DocumentURI dict for this annotation.

            This doesn't add anything to the database session yet.
            """
            document_uri = DocumentURI.build(claimant=self.target_uri,
                                             uri=self.target_uri)
            return dict(
                claimant=document_uri.claimant,
                uri=document_uri.uri,
                type=document_uri.type,
                content_type=document_uri.content_type,
            )

        document_uri_dicts = [document_uri_dict()
                              for _ in range(random.randint(1, 3))]

        def document_meta_dict(**kwargs):
            """
            Return a randomly generated DocumentMeta dict for this annotation.

            This doesn't add anything to the database session yet.
            """
            kwargs.setdefault('claimant', self.target_uri)
            document_meta = DocumentMeta.build(**kwargs)
            return dict(
                claimant=document_meta.claimant,
                type=document_meta.type,
                value=document_meta.value,
            )

        document_meta_dicts = [document_meta_dict()
                               for _ in range(random.randint(1, 3))]

        # Make sure that there's always at least one DocumentMeta with
        # type='title', so that we never get annotation.document.title is None:
        if 'title' not in [m['type'] for m in document_meta_dicts]:
            document_meta_dicts.append(document_meta_dict(type='title'))

        api_models.update_document_metadata(
            orm.object_session(self),
            self,
            document_meta_dicts=document_meta_dicts,
            document_uri_dicts=document_uri_dicts,
        )


class Activation(ModelFactory):

    class Meta(object):
        model = models.Activation
        force_flush = True


class AuthClient(ModelFactory):

    class Meta(object):
        model = models.AuthClient
        force_flush = True


class User(factory.Factory):

    """A factory class that generates h.models.User objects.

    Note that this class doesn't add the User to the database session for you,
    if tests want the user added to a session they should do that themselves.

    """

    class Meta(object):
        model = models.User

    class Params(object):
        inactive = factory.Trait(
            activation=factory.SubFactory(Activation),
        )

    authority = 'example.com'
    username = factory.Faker('user_name')
    email = factory.Faker('email')

    @factory.lazy_attribute
    def uid(self):
        return self.username.replace('.', '').lower()


class Group(ModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Group
        force_flush = True

    name = factory.Sequence(lambda n:'Test Group {n}'.format(n=str(n)))
    creator = factory.SubFactory(User)


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

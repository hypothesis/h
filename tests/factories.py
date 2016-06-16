# -*- coding: utf-8 -*-
"""Factory classes for easily generating test objects."""

from __future__ import absolute_import
from __future__ import unicode_literals

import random

import factory
import faker

from h import db
from h import models
from h.accounts import models as accounts_models
from h.api import models as api_models


FAKER = faker.Factory.create()


class Document(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Document
        sqlalchemy_session = db.Session


class DocumentMeta(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.DocumentMeta
        sqlalchemy_session = db.Session

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


class DocumentURI(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.DocumentURI
        sqlalchemy_session = db.Session

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


class Annotation(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:  # pylint: disable=no-init, old-style-class
        model = models.Annotation
        sqlalchemy_session = db.Session
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
            db.Session,
            self,
            document_meta_dicts=document_meta_dicts,
            document_uri_dicts=document_uri_dicts,
        )


class User(factory.Factory):

    """A factory class that generates h.accounts.models.User objects.

    Note that this class doesn't add the User to the database session for you,
    if tests want the user added to a session they should do that themselves.

    """

    class Meta(object):
        model = accounts_models.User

    uid = factory.Sequence(lambda n: "test_user_{n}".format(n=n + 1))
    username = factory.Sequence(lambda n: "test_user_{n}".format(n=n + 1))
    email = factory.LazyAttribute(
        lambda n: "{username}@test_users.com".format(username=n.username))
    password = "pass"

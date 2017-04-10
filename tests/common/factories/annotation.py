# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import random

import factory
from sqlalchemy import orm

from h import models
from h.models.document import update_document_metadata

from .base import FAKER, ModelFactory
from .document import Document, DocumentMeta, DocumentURI


class Annotation(ModelFactory):

    class Meta:
        model = models.Annotation
        force_flush = True  # Always flush the db to generate annotation.id.

    tags = factory.LazyFunction(lambda: FAKER.words(nb=random.randint(0, 5)))
    target_uri = factory.Faker('uri')
    text = factory.Faker('paragraph')
    userid = factory.Faker('user_name')
    document = factory.SubFactory(Document)

    @factory.lazy_attribute
    def target_selectors(self):
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
            document_uri = DocumentURI.build(document=self.document,
                                             claimant=self.target_uri,
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
            kwargs.setdefault('document', self.document)
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

        self.document = update_document_metadata(
            orm.object_session(self),
            self.target_uri,
            document_meta_dicts=document_meta_dicts,
            document_uri_dicts=document_uri_dicts,
            created=self.created,
            updated=self.updated,
        )

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import factory

from h import models

from .base import FAKER, ModelFactory


class Document(ModelFactory):
    class Meta:
        model = models.Document


class DocumentMeta(ModelFactory):
    class Meta:
        model = models.DocumentMeta

    # Trying to add two DocumentMetas with the same claimant and type to the
    # db will crash. We use a sequence instead of something like FAKER.url()
    # for claimant here so that never happens (unless you pass in your own
    # claimant).
    claimant = factory.Sequence(lambda n: "http://example.com/document_" + str(n) + "/")

    type = factory.Iterator(
        ["title", "twitter.url.main_url", "twitter.title", "favicon"]
    )
    document = factory.SubFactory(Document)

    @factory.lazy_attribute
    def value(self):
        if self.type == "twitter.url.main_url":
            return [FAKER.url()]
        elif self.type == "favicon":
            return [FAKER.image_url()]
        else:
            return [FAKER.bs()]


class DocumentURI(ModelFactory):
    class Meta:
        model = models.DocumentURI

    # Trying to add two DocumentURIs with the same claimant, uri, type and
    # content_type to the db will crash. We use a sequence instead of something
    # like FAKER.url() for claimant here so that never happens (unless you pass
    # in your own claimant).
    claimant = factory.Sequence(lambda n: "http://example.com/document_" + str(n) + "/")

    uri = factory.LazyAttribute(lambda obj: obj.claimant)
    type = factory.Iterator(
        ["rel-alternate", "rel-canonical", "highwire-pdf", "dc-doi"]
    )
    content_type = factory.Iterator(["text/html", "application/pdf", "text/plain"])
    document = factory.SubFactory(Document)

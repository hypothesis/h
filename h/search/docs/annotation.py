# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from elasticsearch_dsl import (Boolean,
                               DocType,
                               Date,
                               field,
                               Field,
                               Keyword,
                               Text,
                               )

from h.search.docs.target import Target


class Annotation(DocType):
    annotator_schema_version = Text()
    authority = Keyword(index=True)
    created = Date()
    updated = Date()
    quote = Text(analyzer='uni_normalizer')
    tags = Text(analyzer='uni_normalizer')
    tags_raw = Keyword(index=True)
    text = Text(analyzer='uni_normalizer')
    deleted = Boolean()
    uri = Text(
            analyzer='uri',
            fields={
                'parts': Text(analyzer='uri_parts'),
            },
        )
    user = Text(analyzer='user', index=True)
    user_raw = Keyword(index=True)
    target = field.Object(Target)
    shared = Boolean()
    references = Text()
    document = Field(enabled=False)
    group = Text()
    thread_ids = Keyword(index=True)

    class Meta:
        index = 'hypothesis'

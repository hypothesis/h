# -*- coding: utf-8 -*-
from elasticsearch_dsl import (analyzer,
                               Boolean,
                               DocType,
                               Date,
                               field,
                               Field,
                               index,
                               InnerDoc,
                               Integer,
                               Keyword,
                               Long,
                               Text,
                               )


class Selector(InnerDoc):
    # TODO: make this type_
    type = Keyword(index=False)

    # Annotator XPath+offset selector
    startContainer = Keyword(index=False)
    startOffset = Long(index=False)
    endContainer = Keyword(index=False)
    endOffset = Long(index=False)

    # Open Annotation TextQuoteSelector
    exact = Text(
        # 'path': 'just_name',
        index=True,
        fields={
            'quote': Text(
                index=True,
                analyzer='uni_normalizer',
            ),
        },
    )
    prefix = Keyword()
    suffix = Keyword()

    # Open Annotation (Data|Text)PositionSelector
    start = Long()
    end = Long()


class Target(InnerDoc):
    source = Text( analyzer='uri', index=True, copy_to='uri')
    # We store the 'scope' unanalyzed and only do term filters
    # against this field.
    scope = Keyword(index=True)
    selector = field.Object(Selector)


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

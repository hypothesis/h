# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from elasticsearch_dsl import (InnerDoc,
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

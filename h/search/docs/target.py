# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from elasticsearch_dsl import (field,
                               InnerDoc,
                               Keyword,
                               Text,
                               )

from h.search.docs.selector import Selector


class Target(InnerDoc):
    source = Text(analyzer='uri', index=True, copy_to='uri')
    # We store the 'scope' unanalyzed and only do term filters
    # against this field.
    scope = Keyword(index=True)
    selector = field.Object(Selector)

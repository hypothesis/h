# -*- coding: utf-8 -*-
"""Code for persisting (indexing) annotations to Elasticsearch."""

from __future__ import unicode_literals

import elasticsearch_dsl


class Annotation(elasticsearch_dsl.DocType):
    """An elasticsearch_dsl annotation document."""

    authority = elasticsearch_dsl.Keyword(index=False)

    @staticmethod
    def create(models_annotation):
        """Return a new search.Annotation from the given models.Annotation."""
        return Annotation(meta={"id": models_annotation.id})

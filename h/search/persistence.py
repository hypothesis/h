# -*- coding: utf-8 -*-
"""Code for persisting (indexing) Annotations in ElasticSearch"""

from __future__ import unicode_literals

import elasticsearch_dsl


class Annotation(elasticsearch_dsl.DocType):
    """Defines an ElasticSearch annotation document via elasticsearch_dsl"""

    class Meta:
        """
        Define the default index to use for this DocType

        N.B. This index name can be overridden (e.g. in tests)
        via ``Annotation._doc_type.index = "something_else"``
        """
        index = "hypothesis"

    authority = elasticsearch_dsl.Keyword()
    """
    An annotation's authority can be used to filter out annotations by
    authority — e.g. retrieve annotations only applicable to a certain
    user's authority
    """

    @staticmethod
    def create(annotation_model):
        """
        Return a new search.Annotation (DocType)

        Return a search.Annotation instance built from the provided, populated
        annotation model
        """
        return Annotation(meta={
            "id": annotation_model.id
        })

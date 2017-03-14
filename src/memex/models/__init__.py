# -*- coding: utf-8 -*-
"""
Annotations API domain model classes.

This package is currently in flux as we transition between a set of models
which save data to ElasticSearch and a set of models which save data in a
PostgreSQL database.

Please note: access to these model objects should almost certainly not be
direct to the submodules of this package, but rather through the helper
functions in `h.storage`.
"""

from memex.db import set_base

set_base()  # noqa

from memex.models.annotation import Annotation
from memex.models.document import create_or_update_document_meta
from memex.models.document import create_or_update_document_uri
from memex.models.document import Document
from memex.models.document import DocumentMeta
from memex.models.document import DocumentURI
from memex.models.document import merge_documents
from memex.models.document import update_document_metadata


__all__ = (
    'Annotation',
    'create_or_update_document_meta',
    'create_or_update_document_uri',
    'Document',
    'DocumentMeta',
    'DocumentURI',
    'merge_documents',
)


def includeme(_):
    # This module is included for side-effects only. SQLAlchemy models
    # register with the global metadata object when imported.
    pass

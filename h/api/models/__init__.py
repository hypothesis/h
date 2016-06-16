# -*- coding: utf-8 -*-
"""
Annotations API domain model classes.

This package is currently in flux as we transition between a set of models
which save data to ElasticSearch and a set of models which save data in a
PostgreSQL database.

Please note: access to these model objects should almost certainly not be
direct to the submodules of this package, but rather through the helper
functions in `h.api.storage`.
"""

from h.api.models import elastic
from h.api.models.annotation import Annotation
from h.api.models.document import Document
from h.api.models.document import DocumentMeta
from h.api.models.document import DocumentURI
from h.api.models.document import merge_documents
from h.api.models.document import update_document_metadata


__all__ = (
    'Annotation',
    'Document',
    'DocumentMeta',
    'DocumentURI',
    'elastic',
    'merge_documents',
    'update_document_metadata',
)

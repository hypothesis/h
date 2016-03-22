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

from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentMeta, DocumentURI
from h.api.models.document import create_or_update_document_meta
from h.api.models.document import create_or_update_document_uri

__all__ = (
    'Annotation',
    'create_or_update_document_meta',
    'create_or_update_document_uri',
    'Document',
    'DocumentMeta',
    'DocumentURI',
)

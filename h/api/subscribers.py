# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from h.api import storage
from h.api.search.index import index
from h.api.search.index import delete


def index_annotation_event(event):
    """Index a created, updated or deleted annotation into Elasticsearch."""
    if not event.request.feature('postgres'):
        return

    if event.action == 'create':
        annotation = storage.fetch_annotation(event.request, event.annotation_id)
        index(event.request.es, annotation, event.request)
    elif event.action == 'delete':
        delete(event.request.es, event.annotation_id)

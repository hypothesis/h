# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def index_annotation_event(event):
    """Index a created, updated or deleted annotation into Elasticsearch."""
    if not event.request.feature('postgres'):
        return

    if event.action == 'create':
        event.request.es.index_annotation(event.request, event.annotation)

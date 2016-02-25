# -*- coding: utf-8 -*-
"""
Presenters for API data.
"""

import collections


class DocumentMetaJSONPresenter(object):
    def __init__(self, document_meta):
        self.document_meta = document_meta

    def asdict(self):
        # This turns a keypath into a nested dict by first reversing the
        # keypath and then creating the dict from inside-out. Rather than
        # using recursion to create the dict from the outside in.
        reversed_path = self.document_meta.type.split('.')[::-1]
        d = self.document_meta.value
        for nested in reversed_path:
            d = {nested: d}

        return d


class DocumentURIJSONPresenter(object):
    def __init__(self, document_uri):
        self.document_uri = document_uri

    def asdict(self):
        data = {'href': self.document_uri.uri}

        rel = self.rel
        if rel:
            data['rel'] = rel

        type = self.document_uri.content_type
        if type:
            data['type'] = type

        return data

    @property
    def rel(self):
        type = self.document_uri.type
        if type and type.startswith('rel-'):
            return self.document_uri.type[4:]

def utc_iso8601(datetime):
    return datetime.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')


def deep_merge_dict(a, b):
    """Recursively merges dict `b` into dict `a`."""

    for k, v in b.items():
        if isinstance(v, collections.Mapping):
            if k not in a or not isinstance(a[k], dict):
                a[k] = dict()
            deep_merge_dict(a[k], v)
        else:
            a[k] = v

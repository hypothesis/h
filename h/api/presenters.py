# -*- coding: utf-8 -*-
"""
Presenters for API data.
"""

import collections


class AnnotationJSONPresenter(object):
    def __init__(self, annotation):
        self.annotation = annotation

    def asdict(self):
        docpresenter = DocumentJSONPresenter(self.annotation.document)

        base = {
            'id': self.annotation.id,
            'created': self.created,
            'updated': self.updated,
            'user': self.annotation.userid,
            'uri': self.annotation.target_uri,
            'text': self.annotation.text,
            'tags': self.tags,
            'group': self.annotation.groupid,
            'permission': self.permission,
            'target': self.target,
            'document': docpresenter.asdict(),
        }

        if self.annotation.references:
            base['references'] = self.annotation.references

        annotation = self.annotation.extra or {}
        annotation.update(base)

        return annotation

    @property
    def created(self):
        if self.annotation.created:
            return utc_iso8601(self.annotation.created)

    @property
    def updated(self):
        if self.annotation.updated:
            return utc_iso8601(self.annotation.updated)

    @property
    def tags(self):
        if self.annotation.tags:
            return self.annotation.tags
        else:
            return []

    @property
    def permission(self):
        read = self.annotation.userid
        if self.annotation.shared:
            read = 'group:{}'.format(self.annotation.groupid)

        return {'read': [read],
                'admin': [self.annotation.userid],
                'update': [self.annotation.userid],
                'delete': [self.annotation.userid]}

    @property
    def target(self):
        return [{'source': self.annotation.target_uri,
                 'selector': self.annotation.target_selectors or []}]


class DocumentJSONPresenter(object):
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if not self.document:
            return {}

        d = {}

        for docmeta in self.document.meta:
            meta_presenter = DocumentMetaJSONPresenter(docmeta)
            deep_merge_dict(d, meta_presenter.asdict())

        d['link'] = []
        for docuri in self.document.document_uris:
            uri_presenter = DocumentURIJSONPresenter(docuri)
            d['link'].append(uri_presenter.asdict())

        return d


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

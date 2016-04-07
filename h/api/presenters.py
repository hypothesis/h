# -*- coding: utf-8 -*-
"""
Presenters for API data.
"""

import collections
import copy

LINK_GENERATORS_KEY = 'h.api.presenters.link_generators'


class AnnotationBasePresenter(object):
    def __init__(self, request, annotation):
        self.annotation = annotation
        self.request = request

    @property
    def created(self):
        if self.annotation.created:
            return utc_iso8601(self.annotation.created)

    @property
    def updated(self):
        if self.annotation.updated:
            return utc_iso8601(self.annotation.updated)

    @property
    def links(self):
        """A dictionary of named hypermedia links for this annotation."""
        # Named link generators are registered elsewhere in the code. See
        # :py:func:`h.api.presenters.add_annotation_link_generator` for
        # details.
        link_generators = self.request.registry.get(LINK_GENERATORS_KEY, {})
        out = {}
        for name, generator in link_generators.items():
            link = generator(self.request, self.annotation)
            if link is not None:
                out[name] = link
        return out

    @property
    def text(self):
        if self.annotation.text:
            return self.annotation.text
        else:
            return ''

    @property
    def tags(self):
        if self.annotation.tags:
            return self.annotation.tags
        else:
            return []

    @property
    def target(self):
        target = {'source': self.annotation.target_uri}
        if self.annotation.target_selectors:
            target['selector'] = self.annotation.target_selectors

        return [target]


class AnnotationJSONPresenter(AnnotationBasePresenter):
    def asdict(self):
        docpresenter = DocumentJSONPresenter(self.annotation.document)

        base = {
            'id': self.annotation.id,
            'created': self.created,
            'updated': self.updated,
            'user': self.annotation.userid,
            'uri': self.annotation.target_uri,
            'text': self.text,
            'tags': self.tags,
            'group': self.annotation.groupid,
            'permissions': self.permissions,
            'target': self.target,
            'document': docpresenter.asdict(),
            'links': self.links,
        }

        if self.annotation.references:
            base['references'] = self.annotation.references

        annotation = copy.copy(self.annotation.extra) or {}
        annotation.update(base)

        return annotation

    @property
    def permissions(self):
        read = self.annotation.userid
        if self.annotation.shared:
            read = 'group:{}'.format(self.annotation.groupid)

        return {'read': [read],
                'admin': [self.annotation.userid],
                'update': [self.annotation.userid],
                'delete': [self.annotation.userid]}


class AnnotationJSONLDPresenter(AnnotationBasePresenter):

    """
    Presenter for annotations that renders a JSON-LD format compatible with the
    draft Web Annotation Data Model, as defined at:

      https://www.w3.org/TR/annotation-model/
    """

    CONTEXT_URL = 'http://www.w3.org/ns/anno.jsonld'

    def asdict(self):
        return {
            '@context': self.CONTEXT_URL,
            'type': 'Annotation',
            'id': self.id,
            'created': self.created,
            'modified': self.updated,
            'creator': self.annotation.userid,
            'body': self.bodies,
            'target': self.target,
        }

    @property
    def id(self):
        return self.request.route_url('annotation', id=self.annotation.id)

    @property
    def bodies(self):
        bodies = [{
            'type': 'TextualBody',
            'text': self.text,
            'format': 'text/markdown',
        }]
        for t in self.tags:
            bodies.append({
                'type': 'TextualBody',
                'text': t,
                'purpose': 'tagging',
            })
        return bodies


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


def add_annotation_link_generator(registry, name, generator):
    """
    Registers a function which generates a named link for an annotation.

    Annotation hypermedia links are added to the rendered annotations in a
    `links` property or similar. `name` is the unique identifier for the link
    type, and `generator` is a callable which accepts two arguments -- the
    current request, and the annotation for which to generate a link -- and
    returns a string.
    """
    if LINK_GENERATORS_KEY not in registry:
        registry[LINK_GENERATORS_KEY] = {}
    registry[LINK_GENERATORS_KEY][name] = generator


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


def _json_link(request, annotation):
    return request.route_url('api.annotation', id=annotation.id)


def includeme(config):
    config.add_directive(
        'add_annotation_link_generator',
        lambda c, n, g: add_annotation_link_generator(c.registry, n, g))

    # Add a default 'json' link type
    config.add_annotation_link_generator('json', _json_link)

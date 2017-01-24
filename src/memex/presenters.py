# -*- coding: utf-8 -*-
"""
Presenters for API data.
"""

import collections
import copy

from pyramid import security


class AnnotationBasePresenter(object):
    def __init__(self, annotation_resource):
        self.annotation_resource = annotation_resource
        self.annotation = annotation_resource.annotation

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
        return self.annotation_resource.links

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

    """Present an annotation in the JSON format returned by API requests."""

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
        """
        Return a permissions dict for the given annotation.

        Converts our simple internal annotation storage format into the legacy
        complex permissions dict format that is still used in some places.

        """
        read = self.annotation.userid
        if self.annotation.shared:
            read = 'group:{}'.format(self.annotation.groupid)

            principals = security.principals_allowed_by_permission(
                    self.annotation_resource, 'read')
            if security.Everyone in principals:
                read = 'group:__world__'

        return {'read': [read],
                'admin': [self.annotation.userid],
                'update': [self.annotation.userid],
                'delete': [self.annotation.userid]}


class AnnotationSearchIndexPresenter(AnnotationBasePresenter):

    """Present an annotation in the JSON format used in the search index."""
    def __init__(self, annotation):
        self.annotation = annotation

    def asdict(self):
        docpresenter = DocumentSearchIndexPresenter(self.annotation.document)

        result = {
            'id': self.annotation.id,
            'created': self.created,
            'updated': self.updated,
            'user': self.annotation.userid,
            'user_raw': self.annotation.userid,
            'uri': self.annotation.target_uri,
            'text': self.text,
            'tags': self.tags,
            'tags_raw': self.tags,
            'group': self.annotation.groupid,
            'shared': self.annotation.shared,
            'target': self.target,
            'document': docpresenter.asdict(),
        }

        result['target'][0]['scope'] = [self.annotation.target_uri_normalized]

        if self.annotation.references:
            result['references'] = self.annotation.references

        return result

    @property
    def links(self):
        # The search index presenter has no need to generate links, and so the
        # `links_service` parameter has been removed from the constructor.
        raise NotImplementedError("search index presenter doesn't have links")


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
        return self.annotation_resource.link('jsonld_id')

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
        title = self.document.title
        if title:
            d['title'] = [title]

        return d


class DocumentSearchIndexPresenter(object):
    def __init__(self, document):
        self.document = document

    def asdict(self):
        if not self.document:
            return {}

        d = {}
        if self.document.title:
            d['title'] = [self.document.title]

        if self.document.web_uri:
            d['web_uri'] = self.document.web_uri

        return d


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


def _jsonld_id_link(request, annotation):
    return request.route_url('annotation', id=annotation.id)


def _permissions(annotation):
    """
    Return a permissions dict for the given annotation.

    Converts our simple internal annotation storage format into the legacy
    complex permissions dict format that is still used in some places.

    """
    read = annotation.userid
    if annotation.shared:
        read = 'group:{}'.format(annotation.groupid)

    return {'read': [read],
            'admin': [annotation.userid],
            'update': [annotation.userid],
            'delete': [annotation.userid]}


def includeme(config):
    # Add a default 'json' link type
    config.add_annotation_link_generator('json', _json_link)

    # Add a 'jsonld_id' link type for generating the "id" field for JSON-LD
    # annotations. This is hidden, and so not rendered in the annotation's
    # "links" field.
    config.add_annotation_link_generator('jsonld_id',
                                         _jsonld_id_link,
                                         hidden=True)

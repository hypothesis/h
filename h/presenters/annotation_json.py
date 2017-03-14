# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy

from pyramid import security

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_json import DocumentJSONPresenter


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

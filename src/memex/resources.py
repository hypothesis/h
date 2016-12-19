# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from memex import groups
from memex import storage


class AnnotationResourceFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        annotation = storage.fetch_annotation(self.request.db, id)
        if annotation is None:
            raise KeyError()
        return AnnotationResource(self.request, annotation)


class AnnotationResource(object):
    def __init__(self, request, annotation):
        self.request = request
        self.annotation = annotation

    @property
    def group(self):
        return groups.find(self.request, self.annotation.groupid)

    def __acl__(self):
        """Return a Pyramid ACL for this annotation."""
        acl = []
        if self.annotation.shared:
            for principal in _group_principals(self.group):
                acl.append((security.Allow, principal, 'read'))
        else:
            acl.append((security.Allow, self.annotation.userid, 'read'))

        for action in ['admin', 'update', 'delete']:
            acl.append((security.Allow, self.annotation.userid, action))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(security.DENY_ALL)

        return acl


def _group_principals(group):
    if group is None:
        return []
    return security.principals_allowed_by_permission(group, 'read')

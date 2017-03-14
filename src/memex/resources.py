# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from h import storage  # FIXME: this module needs to move to h
from memex.interfaces import IGroupService


class AnnotationResourceFactory(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        annotation = storage.fetch_annotation(self.request.db, id)
        if annotation is None:
            raise KeyError()

        group_service = self.request.find_service(IGroupService)
        links_service = self.request.find_service(name='links')
        return AnnotationResource(annotation, group_service, links_service)


class AnnotationResource(object):
    def __init__(self, annotation, group_service, links_service):
        self.group_service = group_service
        self.links_service = links_service
        self.annotation = annotation

    @property
    def group(self):
        return self.group_service.find(self.annotation.groupid)

    @property
    def links(self):
        return self.links_service.get_all(self.annotation)

    def link(self, name):
        return self.links_service.get(self.annotation, name)

    def __acl__(self):
        """Return a Pyramid ACL for this annotation."""
        # If the annotation has been deleted, nobody has any privileges on it
        # any more.
        if self.annotation.deleted:
            return [security.DENY_ALL]

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

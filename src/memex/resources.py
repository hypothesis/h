# -*- coding: utf-8 -*-

from pyramid import security

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

    def __acl__(self):
        """Return a Pyramid ACL for this annotation."""
        acl = []
        if self.annotation.shared:
            group = 'group:{}'.format(self.annotation.groupid)
            if self.annotation.groupid == '__world__':
                group = security.Everyone

            acl.append((security.Allow, group, 'read'))
        else:
            acl.append((security.Allow, self.annotation.userid, 'read'))

        for action in ['admin', 'update', 'delete']:
            acl.append((security.Allow, self.annotation.userid, action))

        # If we haven't explicitly authorized it, it's not allowed.
        acl.append(security.DENY_ALL)

        return acl

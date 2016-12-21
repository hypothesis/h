# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security

from h import models


class WorldGroup(object):
    """
    A Group object for the __world__ group, it only implements __acl__.

    This is so we don't have to store a __world__ group in the database.
    """

    def __init__(self, auth_domain):
        self.auth_domain = auth_domain

    def __acl__(self):
        return [
            (security.Allow, security.Everyone, 'read'),
            (security.Allow, 'authority:{}'.format(self.auth_domain), 'write'),
            security.DENY_ALL,
        ]


def fetch_group(request, id_):
    if id_ == '__world__':
        return WorldGroup(request.auth_domain)

    # This should probably use the GroupService with a built-in caching layer.
    return request.db.query(models.Group).filter_by(pubid=id_).one_or_none()

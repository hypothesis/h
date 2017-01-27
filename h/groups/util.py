# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security


class WorldGroup(object):
    """
    A Group object for the __world__ group.

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

    @property
    def name(self):
        return 'Public'

    @property
    def pubid(self):
        return '__world__'

    @property
    def is_public(self):
        return True

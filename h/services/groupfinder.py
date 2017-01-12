# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer

from memex.interfaces import IGroupService

from h import models
from h.groups.util import WorldGroup


@implementer(IGroupService)
class GroupfinderService(object):
    def __init__(self, session, auth_domain):
        self.session = session
        self.auth_domain = auth_domain

    def find(self, id_):
        if id_ == '__world__':
            return WorldGroup(self.auth_domain)

        # TODO: caching
        return self.session.query(models.Group).filter_by(pubid=id_).one_or_none()


def groupfinder_service_factory(context, request):
    return GroupfinderService(request.db, request.auth_domain)

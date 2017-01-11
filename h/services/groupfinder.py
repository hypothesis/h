# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer
import sqlalchemy

from memex.interfaces import IGroupService

from h import models
from h.groups.util import WorldGroup


@implementer(IGroupService)
class GroupfinderService(object):
    def __init__(self, session, auth_domain):
        self.session = session
        self.auth_domain = auth_domain

        # Local cache of fetched groups.
        self._cache = {}

        # But don't allow the cache to persist after the session is closed.
        @sqlalchemy.event.listens_for(session, 'after_commit')
        @sqlalchemy.event.listens_for(session, 'after_rollback')
        def flush_cache(session):
            self._cache = {}

    def find(self, id_):
        if id_ == '__world__':
            return WorldGroup(self.auth_domain)

        if id_ not in self._cache:
            self._cache[id_] = (self.session.query(models.Group)
                                .filter_by(pubid=id_)
                                .one_or_none())

        return self._cache[id_]


def groupfinder_service_factory(context, request):
    return GroupfinderService(request.db, request.auth_domain)

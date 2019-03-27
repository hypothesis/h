# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import GroupScope
from h.util import group_scope as scope_util


class GroupScopeService(object):
    def __init__(self, session):
        self._session = session

    def fetch_by_scope(self, url):
        """Return GroupScope records that match the given URL

        :arg url: URL to find matching scopes for
        :type url: str
        :rtype: list(:class:`~h.models.group_scope.GroupScope`)
        """
        origin = scope_util.parse_origin(url)
        if not origin:
            return []
        origin_scopes = (
            self._session.query(GroupScope).filter(GroupScope.origin == origin).all()
        )
        return [
            scope
            for scope in origin_scopes
            if scope_util.url_in_scope(url, [scope.scope])
        ]


def group_scope_factory(context, request):
    return GroupScopeService(session=request.db)

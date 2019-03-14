# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import GroupScope
from h.util import group_scope as scope_util


class GroupScopeService(object):
    def __init__(self, session):
        self._session = session

    def fetch_by_origin(self, uri):
        # Retrieve all GroupScope records in the DB that have an `origin` component
        # that matches the given uri's origin. This will give us a set of
        # results whose scopes may match the `document_uri`
        # Refactor into scopes_for_origin
        origin = scope_util.parse_origin(uri)
        if not origin:
            return []
        origin_scopes = (
            self._session.query(GroupScope).filter(GroupScope.origin == origin).all()
        )
        return origin_scopes

    def fetch_by_scope(self, uri):
        origin_scopes = self.fetch_by_origin(uri)
        return [
            scope
            for scope in origin_scopes
            if scope_util.uri_in_scope(uri, [scope.scope])
        ]


def group_scope_factory(context, request):
    return GroupScopeService(session=request.db)

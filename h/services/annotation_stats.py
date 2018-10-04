# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from webob.multidict import MultiDict

from h.models import Annotation
from h.search import Search
from h.search import TopLevelAnnotationsFilter


class AnnotationStatsService(object):
    """A service for retrieving annotation stats for users and groups."""

    def __init__(self, request):
        self.request = request

    def user_annotation_counts(self, userid):
        """Return the count of annotations for this user."""

        annotations = self.request.db.query(Annotation). \
            filter_by(userid=userid, deleted=False). \
            options(sa.orm.load_only('groupid', 'shared')).subquery()
        grouping = sa.case([
            (sa.not_(annotations.c.shared), 'private'),
            (annotations.c.groupid == '__world__', 'public'),
        ], else_='group')

        result = dict(self.request.db.query(grouping, sa.func.count(annotations.c.id)).group_by(grouping).all())
        for key in ['public', 'group', 'private']:
            result.setdefault(key, 0)

        result['total'] = result['public'] + \
            result['group'] + \
            result['private']

        return result

    def group_annotation_count(self, pubid):
        """
        Return the count of searchable top level annotations for this group.
        """
        search = Search(self.request, stats=self.request.stats)
        search.append_modifier(TopLevelAnnotationsFilter())

        params = MultiDict({'limit': 0, 'group': pubid})

        search_result = search.run(params)
        return search_result.total


def annotation_stats_factory(context, request):
    """Return an AnnotationStatsService instance for the passed context and request."""
    return AnnotationStatsService(request)

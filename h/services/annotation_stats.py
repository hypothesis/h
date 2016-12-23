# -*- coding: utf-8 -*-

import sqlalchemy as sa

from h.models import Annotation


class AnnotationStatsService(object):
    """A service for retrieving annotation stats for users and groups."""

    def __init__(self, session):
        self.session = session

    def user_annotation_counts(self, userid):
        """Return the count of annotations for this user."""

        annotations = self.session.query(Annotation).filter_by(userid=userid).options(sa.orm.load_only('groupid', 'shared')).subquery()
        grouping = sa.case([
            (sa.not_(annotations.c.shared), 'private'),
            (annotations.c.groupid == '__world__', 'public'),
        ], else_='group')
        return dict(self.session.query(grouping, sa.func.count(annotations.c.id)).group_by(grouping).all())

    def group_annotation_count(self, pubid):
        """
        Return the count of shared annotations for this group.
        """

        return (
            self.session.query(Annotation)
            .filter_by(groupid=pubid, shared=True)
            .count())


def annotation_stats_factory(context, request):
    """Return an AnnotationStatsService instance for the passed context and request."""
    return AnnotationStatsService(session=request.db)

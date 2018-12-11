# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h.models import Flag


class FlagCountService(object):
    def __init__(self, session):
        self._session = session

    def flag_count(self, annotation):
        """
        Return the number of times a given annotation has been flagged.

        :param annotation: The annotation to check for flags.
        :type annotation: h.models.Annotation

        :returns: The number of times the annotation has been flagged.
        :rtype: int
        """
        return (
            self._session.query(sa.func.count(Flag.id))
            .filter_by(annotation_id=annotation.id)
            .scalar()
        )

    def flag_counts(self, annotation_ids):
        """
        Return flag counts for a batch of annotations.

        :param annotation_ids: The IDs of the annotations to check.
        :type annotation_ids: sequence of unicode

        :returns: A map of annotation IDs to flag counts.
        :rtype: dict[unicode, int]
        """
        if not annotation_ids:
            return {}

        query = (
            self._session.query(
                sa.func.count(Flag.id).label("flag_count"), Flag.annotation_id
            )
            .filter(Flag.annotation_id.in_(annotation_ids))
            .group_by(Flag.annotation_id)
        )

        flag_counts = {f.annotation_id: f.flag_count for f in query}
        missing_ids = set(annotation_ids) - set(flag_counts.keys())
        flag_counts.update({id_: 0 for id_ in missing_ids})
        return flag_counts


def flag_count_service_factory(context, request):
    return FlagCountService(request.db)

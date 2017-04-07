# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from zope.interface import implementer

from h import models
from h.formatters.interfaces import IAnnotationFormatter


@implementer(IAnnotationFormatter)
class AnnotationModerationFormatter(object):
    """
    Formatter for exposing an annotation's moderation information.

    If the passed-in user has permission to hide the annotation (if they are a
    moderator of the annotation's group, for instance), this formatter will
    add a `moderation` key to the payload, with a count of how many users have
    flagged the annotation.
    """

    def __init__(self, session, user, has_permission):
        self._session = session
        self._user = user
        self._has_permission = has_permission

        # Local cache of flag counts. We don't need to care about detached
        # instances because we only store the annotation id and a count.
        self._cache = {}

    def preload(self, ids):
        if self._user is None:
            return

        if not ids:
            return

        query = self._session.query(sa.func.count(models.Flag.id).label('flag_count'),
                                    models.Flag.annotation_id) \
                             .filter(models.Flag.annotation_id.in_(ids)) \
                             .group_by(models.Flag.annotation_id)

        flag_counts = {f.annotation_id: f.flag_count for f in query}
        missing_ids = set(ids) - set(flag_counts.keys())
        flag_counts.update({id_: 0 for id_ in missing_ids})

        self._cache.update(flag_counts)

        return flag_counts

    def format(self, annotation_resource):
        if not self._has_permission('admin', annotation_resource.group):
            return {}

        flag_count = self._load(annotation_resource.annotation.id)
        return {'moderation': {'flagCount': flag_count}}

    def _load(self, id_):
        if id_ in self._cache:
            return self._cache[id_]

        flag_count = self._session.query(sa.func.count(models.Flag.id)) \
                                  .filter_by(annotation_id=id_) \
                                  .scalar()
        self._cache[id_] = flag_count
        return flag_count

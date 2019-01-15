# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer

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

    def __init__(self, flag_count_svc, user, has_permission):
        self._flag_count_svc = flag_count_svc
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

        flag_counts = self._flag_count_svc.flag_counts(ids)
        self._cache.update(flag_counts)
        return flag_counts

    def format(self, annotation_resource):
        if not self._has_permission("moderate", annotation_resource.group):
            return {}

        flag_count = self._load(annotation_resource.annotation)
        return {"moderation": {"flagCount": flag_count}}

    def _load(self, annotation):
        id_ = annotation.id

        if id_ in self._cache:
            return self._cache[id_]

        flag_count = self._flag_count_svc.flag_count(annotation)
        self._cache[id_] = flag_count
        return flag_count

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

    def format(self, annotation_resource):
        if not self._has_permission('admin', annotation_resource.group):
            return {}

        flag_count = self._load(annotation_resource.annotation)
        return {'moderation': {'flagCount': flag_count}}

    def _load(self, annotation):
        return self._flag_count_svc.flag_count(annotation)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer

from h.formatters.interfaces import IAnnotationFormatter


@implementer(IAnnotationFormatter)
class AnnotationFlagFormatter(object):
    """
    Formatter for exposing a user's annotation flags.

    If the passed-in user has flagged an annotation, this formatter will
    add: `"flagged": true` to the payload, otherwise `"flagged": false`.
    """

    def __init__(self, flag_service, user=None):
        self.flag_service = flag_service
        self.user = user

        # Local cache of flags. We don't need to care about detached
        # instances because we only store the annotation id and a boolean flag.
        self._cache = {}

    def preload(self, ids):
        if self.user is None:
            return

        flagged_ids = self.flag_service.all_flagged(user=self.user,
                                                    annotation_ids=ids)

        flags = {id_: (id_ in flagged_ids) for id_ in ids}
        self._cache.update(flags)
        return flags

    def format(self, annotation_resource):
        flagged = self._load(annotation_resource.annotation)
        return {'flagged': flagged}

    def _load(self, annotation):
        if self.user is None:
            return False

        id_ = annotation.id

        if id_ in self._cache:
            return self._cache[id_]

        flagged = self.flag_service.flagged(user=self.user, annotation=annotation)
        self._cache[id_] = flagged
        return self._cache[id_]

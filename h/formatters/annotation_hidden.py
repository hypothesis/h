# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer

from h.formatters.interfaces import IAnnotationFormatter


@implementer(IAnnotationFormatter)
class AnnotationHiddenFormatter(object):
    """
    Formatter for exposing whether an annotation is hidden or not.

    If the annotation is hidden, this formatter will add: `"hidden": true`
    to the payload, otherwise `"hidden": false`.
    When the currently authenticated user is the annotation author, then this
    formatter will always add `"hidden": false`, to not signal that the
    annotation is hidden.
    """

    def __init__(self, moderation_svc, user=None):
        self.moderation_svc = moderation_svc
        self.user = user

        # Local cache of hidden flags. We don't need to care about detached
        # instances because we only store the annotation id and a boolean flag.
        self._cache = {}

    def preload(self, ids):
        hidden_ids = self.moderation_svc.all_hidden(ids)

        hidden = {id_: (id_ in hidden_ids) for id_ in ids}
        self._cache.update(hidden)
        return hidden

    def format(self, annotation_resource):
        annotation = annotation_resource.annotation

        if self.user and self.user.userid == annotation.userid:
            hidden = False
        else:
            hidden = self._load(annotation)
        return {'hidden': hidden}

    def _load(self, annotation):
        id_ = annotation.id

        if id_ in self._cache:
            return self._cache[id_]

        hidden = self.moderation_svc.hidden(annotation)
        self._cache[id_] = hidden
        return self._cache[id_]

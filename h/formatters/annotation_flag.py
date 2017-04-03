# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import implementer

from h import models
from h.formatters.interfaces import IAnnotationFormatter


@implementer(IAnnotationFormatter)
class AnnotationFlagFormatter(object):
    """
    Formatter for exposing a user's annotation flags.

    If the passed-in user has flagged an annotation, this formatter will
    add: `"flagged": true` to the payload, otherwise `"flagged": false`.
    """

    def __init__(self, session, user=None):
        self.session = session
        self.user = user

        # Local cache of flags. We don't need to care about detached
        # instances because we only store the annotation id and a boolean flag.
        self._cache = {}

    def preload(self, ids):
        if self.user is None:
            return

        query = self.session.query(models.Flag) \
                            .filter(models.Flag.annotation_id.in_(ids),
                                    models.Flag.user == self.user)

        flags = {f.annotation_id: True for f in query}

        # Set flags which have not been found explicitly to False to indicate
        # that we already tried to load them.
        missing_ids = set(ids) - set(flags.keys())
        missing = {id_: False for id_ in missing_ids}
        flags.update(missing)

        self._cache.update(flags)
        return flags

    def format(self, annotation):
        flagged = self._load(annotation.id)
        return {'flagged': flagged}

    def _load(self, id_):
        if self.user is None:
            return False

        if id_ in self._cache:
            return self._cache[id_]

        flag = self.session.query(models.Flag) \
                           .filter_by(annotation_id=id_,
                                      user=self.user) \
                           .one_or_none()

        self._cache[id_] = (flag is not None)
        return self._cache[id_]

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

    def __init__(self, flag_service, user=None):
        self.flag_service = flag_service
        self.user = user

    def format(self, annotation_resource):
        flagged = self._load(annotation_resource.annotation)
        return {'flagged': flagged}

    def _load(self, annotation):
        return self.flag_service.flagged(user=self.user, annotation=annotation)

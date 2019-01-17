# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime

from h.events import AnnotationEvent
from h.models import Annotation


class AnnotationDeleteService(object):
    def __init__(self, request):
        self.request = request

    def delete(self, annotation):
        """
        Deletes the given annotation.

        :param annotation: the annotation to be deleted
        :type annotation: h.models.Annotation
        """
        annotation = self.request.db.query(Annotation).get(annotation.id)
        annotation.updated = datetime.utcnow()
        annotation.deleted = True

        event = AnnotationEvent(self.request, annotation.id, "delete")
        self.request.notify_after_commit(event)


def annotation_delete_service_factory(context, request):
    return AnnotationDeleteService(request)

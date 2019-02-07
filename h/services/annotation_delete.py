# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime

from h.events import AnnotationEvent


class AnnotationDeleteService(object):
    def __init__(self, request):
        self.request = request

    def delete(self, annotation):
        """
        Delete the given annotation.

        :param annotation: the annotation to be deleted
        :type annotation: h.models.Annotation
        """
        annotation.updated = datetime.utcnow()
        annotation.deleted = True

        event = AnnotationEvent(self.request, annotation.id, "delete")
        self.request.notify_after_commit(event)

    def delete_annotations(self, annotations):
        """
        Delete the given iterable of annotations.

        :param annotations: the iterable of annotations to be deleted
        :type annotations: iterable of h.models.Annotation
        """
        for ann in annotations:
            self.delete(ann)


def annotation_delete_service_factory(context, request):
    return AnnotationDeleteService(request)

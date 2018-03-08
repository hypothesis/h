# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.events import AnnotationEvent
from h.models import Annotation
from h import storage


class DeleteGroupService(object):
    def __init__(self, request):
        self.request = request

    def delete(self, group):
        """
        Deletes a group, its membership relations and all annotations in the
        group.
        """

        self._delete_annotations(group)
        self.request.db.delete(group)

    def _delete_annotations(self, group):
        annotations = self.request.db.query(Annotation) \
                                     .filter_by(groupid=group.pubid)
        for annotation in annotations:
            storage.delete_annotation(self.request.db, annotation.id)
            event = AnnotationEvent(self.request, annotation.id, 'delete')
            self.request.notify_after_commit(event)


def delete_group_service_factory(context, request):
    return DeleteGroupService(request=request)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Annotation


class DeletePublicGroupError(Exception):
    pass


class DeleteGroupService(object):
    def __init__(self, request, delete_annotation_service):
        self.request = request
        self._delete_annotation_service = delete_annotation_service

    def delete(self, group):
        """
        Deletes a group, its membership relations and all annotations in the
        group.
        """

        self._delete_annotations(group)
        self.request.db.delete(group)

    def _delete_annotations(self, group):
        if group.pubid == "__world__":
            raise DeletePublicGroupError("Public group can not be deleted")

        annotations = self.request.db.query(Annotation).filter_by(groupid=group.pubid)
        for ann in annotations:
            self._delete_annotation_service.delete(ann)


def delete_group_service_factory(context, request):
    delete_annotation_service = request.find_service(name="delete_annotation")
    return DeleteGroupService(request, delete_annotation_service)

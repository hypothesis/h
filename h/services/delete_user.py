# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.events import AnnotationEvent
from h.models import Annotation, Group
from h import storage


class UserDeleteError(Exception):
    pass


class DeleteUserService(object):
    def __init__(self, request):
        self.request = request

    def delete(self, user):
        """
        Deletes a user with all their group memberships and annotations.

        Raises UserDeleteError when deletion fails with the appropriate error
        message.
        """

        if Group.created_by(self.request.db, user).count() > 0:
            raise UserDeleteError('Cannot delete user who is a group creator.')

        user.groups = []
        annotations = self.request.db.query(Annotation) \
                                     .filter_by(userid=user.userid)
        for annotation in annotations:
            storage.delete_annotation(self.request.db, annotation.id)
            event = AnnotationEvent(self.request, annotation.id, 'delete')
            self.request.notify_after_commit(event)

        self.request.db.delete(user)


def delete_user_service_factory(context, request):
    return DeleteUserService(request=request)

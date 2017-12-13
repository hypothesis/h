# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.events import AnnotationEvent
from h.models import Annotation
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

        # Check whether this user has created any groups that others have
        # annotated in.
        #
        # We check for non-empty `group_ids` before querying the DB to avoid an
        # expensive SQL query if `in_` is given an empty list (see
        # https://stackoverflow.com/questions/23523147/)
        group_ids = [g.pubid for g in user.groups]
        if len(group_ids) > 0:
            other_user_group_anns = self.request.db.query(Annotation) \
                                                   .filter(Annotation.groupid.in_(group_ids),
                                                           Annotation.userid != user.userid) \
                                                   .count()
            if other_user_group_anns > 0:
                raise UserDeleteError('Other users have annotated in groups created by this user')

        # Delete the user's annotations
        annotations = self.request.db.query(Annotation) \
                                     .filter_by(userid=user.userid)
        for annotation in annotations:
            storage.delete_annotation(self.request.db, annotation.id)
            event = AnnotationEvent(self.request, annotation.id, 'delete')
            self.request.notify_after_commit(event)

        # Delete groups created by this user.
        for group in user.groups:
            self.request.db.delete(group)

        # Finally, delete the user.
        self.request.db.delete(user)


def delete_user_service_factory(context, request):
    return DeleteUserService(request=request)

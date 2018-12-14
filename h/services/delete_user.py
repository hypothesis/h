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

        created_groups = self.request.db.query(Group).filter(Group.creator == user)
        if self._groups_have_anns_from_other_users(created_groups, user):
            raise UserDeleteError(
                "Other users have annotated in groups created by this user"
            )

        self._delete_annotations(user)
        self._delete_groups(created_groups)
        self.request.db.delete(user)

    def _groups_have_anns_from_other_users(self, groups, user):
        """
        Return `True` if users other than `user` have annotated in `groups`.
        """
        group_ids = [g.pubid for g in groups]

        # We check for non-empty `group_ids` before querying the DB to avoid an
        # expensive SQL query if `in_` is given an empty list (see
        # https://stackoverflow.com/questions/23523147/)
        if len(group_ids) == 0:
            return False

        other_user_ann_count = (
            self.request.db.query(Annotation)
            .filter(Annotation.groupid.in_(group_ids), Annotation.userid != user.userid)
            .count()
        )
        return other_user_ann_count > 0

    def _delete_annotations(self, user):
        annotations = self.request.db.query(Annotation).filter_by(userid=user.userid)
        for annotation in annotations:
            storage.delete_annotation(self.request.db, annotation.id)
            event = AnnotationEvent(self.request, annotation.id, "delete")
            self.request.notify_after_commit(event)

    def _delete_groups(self, groups):
        for group in groups:
            self.request.db.delete(group)


def delete_user_service_factory(context, request):
    return DeleteUserService(request=request)

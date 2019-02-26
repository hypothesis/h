# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Annotation, Group


class DeleteUserService(object):
    def __init__(self, request, annotation_delete_service):
        self.request = request
        self._annotation_delete_service = annotation_delete_service

    def delete(self, user):
        """
        Deletes a user with all their group memberships and annotations.

        If a user owns groups with collaborators, meaning there are annotations
        in the group that have been made by other users, the user is unassigned
        as creator but the group persists.
        """

        created_groups = self.request.db.query(Group).filter(Group.creator == user)
        groups_to_unassign_creator = self._groups_that_have_collaborators(
            created_groups, user
        )
        groups_to_delete = list(set(created_groups) - set(groups_to_unassign_creator))

        self._delete_annotations(user)
        self._delete_groups(groups_to_delete)
        self._unassign_groups_creator(groups_to_unassign_creator)
        self.request.db.delete(user)

    def _groups_that_have_collaborators(self, groups, user):
        """
        Return list of groups that have annotations from other users.
        :param groups: List of group objects to evaluate.
        :type groups: list[h.models.Group]
        :param user: The user object and creator of the groups.
        :type user: h.models.User

        :returns: List of h.models.Group objects that contain annotations made by
          other users.
        """
        group_ids = [g.pubid for g in groups]

        # We check for non-empty `group_ids` before querying the DB to avoid an
        # expensive SQL query if `in_` is given an empty list (see
        # https://stackoverflow.com/questions/23523147/)
        if len(group_ids) == 0:
            return []

        query = (
            self.request.db.query(Annotation.groupid)
            .filter(Annotation.groupid.in_(group_ids), Annotation.userid != user.userid)
            .group_by(Annotation.groupid)
        )
        groupids_with_other_user_anns = [pubid for (pubid,) in query.all()]

        return [g for g in groups if g.pubid in groupids_with_other_user_anns]

    def _delete_annotations(self, user):
        annotations = self.request.db.query(Annotation).filter_by(userid=user.userid)
        for annotation in annotations:
            self._annotation_delete_service.delete(annotation)

    def _delete_groups(self, groups):
        for group in groups:
            self.request.db.delete(group)

    def _unassign_groups_creator(self, groups):
        for group in groups:
            group.creator = None


def delete_user_service_factory(context, request):
    annotation_delete_service = request.find_service(name="annotation_delete")
    return DeleteUserService(request, annotation_delete_service)

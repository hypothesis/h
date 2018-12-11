# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models


class FlagService(object):
    def __init__(self, session):
        self.session = session

    def flagged(self, user, annotation):
        """
        Check if a given user has flagged a given annotation.

        :param user: The user to check for a flag.
        :type user: h.models.User

        :param annotation: The annotation to check for a flag.
        :type annotation: h.models.Annotation

        :returns: True/False depending on the existence of a flag.
        :rtype: bool
        """
        query = self.session.query(models.Flag).filter_by(
            user=user, annotation=annotation
        )
        return query.count() > 0

    def all_flagged(self, user, annotation_ids):
        """
        Check which of the given annotation IDs the given user has flagged.

        :param user: The user to check for a flag.
        :type user: h.models.User

        :param annotation_ids: The IDs of the annotations to check.
        :type annotation_ids: sequence of unicode

        :returns The subset of the IDs that the given user has flagged.
        :rtype set of unicode
        """
        # SQLAlchemy doesn't behave in the way we might expect when handed an
        # `in_` condition with an empty sequence
        if not annotation_ids:
            return set()

        query = self.session.query(models.Flag.annotation_id).filter(
            models.Flag.annotation_id.in_(annotation_ids), models.Flag.user == user
        )

        return set([f.annotation_id for f in query])

    def create(self, user, annotation):
        """
        Create a flag for the given user and annotation.

        We enforce the uniqueness of a flag, meaning one user can only
        flag one annotation once. This method first checks if the annotation
        is already flagged by the user, if that is the case, then this
        is a no-op.

        :param user: The user flagging the annotation.
        :type user: h.models.User

        :param annotation: The annotation to be flagged.
        :type annotation: h.models.Annotation

        :returns: None
        :rtype: NoneType
        """
        if self.flagged(user, annotation):
            return

        flag = models.Flag(user=user, annotation=annotation)
        self.session.add(flag)


def flag_service_factory(context, request):
    return FlagService(request.db)

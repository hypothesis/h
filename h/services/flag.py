# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from memex import uri

from h import models
from h import storage


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
        query = self.session.query(models.Flag).filter_by(user=user, annotation=annotation)
        return query.count() > 0

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

        flag = models.Flag(user=user,
                           annotation=annotation)
        self.session.add(flag)


def flag_service_factory(context, request):
    return FlagService(request.db)

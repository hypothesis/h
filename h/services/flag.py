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
        query = self.session.query(models.Flag).filter_by(user=user, annotation=annotation)
        return query.count() > 0


def flag_service_factory(context, request):
    return FlagService(request.db)

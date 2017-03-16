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

    def list(self, user, group=None, uris=None):
        """
        Return a list of flags made by the given user.

        :param user: The user to filter flags on.
        :type user: h.models.User

        :param group: The annotation group pubid for filtering flags.
        :type group: unicode

        :param uris: A list of annotation uris for filtering flags.
        :type uris: list of unicode

        :returns: list of flags (``h.models.Flag``)
        :rtype: list
        """

        query = self.session.query(models.Flag).filter_by(user=user)

        joined_annotation = False

        if group is not None:
            joined_annotation = True
            query = query.join(models.Annotation) \
                         .filter(models.Annotation.groupid == group)

        if uris:
            query_uris = set()
            for u in uris:
                expanded = storage.expand_uri(self.session, u)
                query_uris.update([uri.normalize(e) for e in expanded])

            if not joined_annotation:
                joined_annotation = True
                query = query.join(models.Annotation)
            query = query.filter(models.Annotation.target_uri_normalized.in_(query_uris))

        return query


def flag_service_factory(context, request):
    return FlagService(request.db)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from h.models import User
from h.tasks.indexer import reindex_user_annotations


class NipsaService(object):

    """
    A service which provides access to the state of "not-in-public-site-areas"
    (NIPSA) flags on userids.
    """

    def __init__(self, session):
        self.session = session

    def fetch_all_flagged_userids(self):
        """
        Fetch the userids of all shadowbanned / NIPSA'd users.

        :rtype: set of unicode strings
        """
        query = self.session.query(User).filter_by(nipsa=True)
        return set([u.userid for u in query])

    def is_flagged(self, userid):
        """Return whether the given userid is flagged as "NIPSA"."""
        user = self.session.query(User).filter_by(userid=userid).one_or_none()
        return user and user.nipsa

    def flag(self, user):
        """
        Add a NIPSA flag for a user.

        Add the given user's ID to the list of NIPSA'd user IDs. If the user
        is already NIPSA'd then nothing will happen (but an "add_nipsa"
        message for the user will still be published to the queue).
        """
        user.nipsa = True
        reindex_user_annotations.delay(user.userid)

    def unflag(self, user):
        """
        Remove the NIPSA flag for a user.

        If the user isn't NIPSA'd then nothing will happen (but a
        "remove_nipsa" message for the user will still be published to the
        queue).
        """
        user.nipsa = False
        reindex_user_annotations.delay(user.userid)


def nipsa_factory(context, request):
    """Return a NipsaService instance for the passed context and request."""
    return NipsaService(request.db)

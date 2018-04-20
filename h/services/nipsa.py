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
        self._flagged_userids = None

    @property
    def flagged_userids(self):
        """
        A list of all the NIPSA'd userids.

        :rtype: set of unicode strings
        """
        if self._flagged_userids is None:
            query = self.session.query(User).filter_by(nipsa=True)
            self._flagged_userids = set([u.userid for u in query])
        return self._flagged_userids

    def is_flagged(self, userid):
        """Return whether the given userid is flagged as "NIPSA"."""
        return userid in self.flagged_userids

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

    def clear(self):
        self._flagged_userids = None


def nipsa_factory(context, request):
    """Return a NipsaService instance for the passed context and request."""
    return NipsaService(request.db)

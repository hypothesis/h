# -*- coding: utf-8 -*-

from h.models import User
from h.nipsa import worker


class NipsaService(object):

    """
    A service which provides access to the state of "not-in-public-site-areas"
    (NIPSA) flags on userids.
    """

    def __init__(self, session):
        self.session = session

    @property
    def flagged_users(self):
        """
        A list of all the NIPSA'd users.

        :rtype: list of unicode strings
        """
        return self.session.query(User).filter_by(nipsa=True)

    def is_flagged(self, userid):
        """Return whether the given userid is flagged as "NIPSA"."""
        cnt = self.session.query(User).filter_by(userid=userid,
                                                 nipsa=True).count()
        return cnt != 0

    def flag(self, user):
        """
        Add a NIPSA flag for a user.

        Add the given user's ID to the list of NIPSA'd user IDs. If the user
        is already NIPSA'd then nothing will happen (but an "add_nipsa"
        message for the user will still be published to the queue).
        """
        user.nipsa = True
        worker.add_nipsa.delay(user.userid)

    def unflag(self, user):
        """
        Remove the NIPSA flag for a user.

        If the user isn't NIPSA'd then nothing will happen (but a
        "remove_nipsa" message for the user will still be published to the
        queue).
        """
        user.nipsa = False
        worker.remove_nipsa.delay(user.userid)


def nipsa_factory(context, request):
    """Return a NipsaService instance for the passed context and request."""
    return NipsaService(request.db)

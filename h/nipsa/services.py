# -*- coding: utf-8 -*-

from h.nipsa import models
from h.nipsa import worker


class NipsaService(object):

    """
    A service which provides access to the state of "not-in-public-site-areas"
    (NIPSA) flags on userids.
    """

    def __init__(self, session):
        self.session = session

    @property
    def flagged_userids(self):
        """
        A list of all the NIPSA'd user IDs.

        :rtype: list of unicode strings
        """
        return [u.userid for u in self.session.query(models.NipsaUser)]

    def is_flagged(self, userid):
        """Return whether the given userid is flagged as "NIPSA"."""
        return self._user_query(userid).one_or_none() is not None

    def flag(self, userid):
        """
        Add a NIPSA flag for a userid.

        Add the given user's ID to the list of NIPSA'd user IDs. If the user
        is already NIPSA'd then nothing will happen (but an "add_nipsa"
        message for the user will still be published to the queue).
        """
        nipsa_user = self._user_query(userid).one_or_none()
        if nipsa_user is None:
            nipsa_user = models.NipsaUser(userid)
            self.session.add(nipsa_user)

        worker.add_nipsa.delay(userid)

    def unflag(self, userid):
        """
        Remove the NIPSA flag for a userid.

        If the user isn't NIPSA'd then nothing will happen (but a
        "remove_nipsa" message for the user will still be published to the
        queue).
        """
        self._user_query(userid).delete()

        worker.remove_nipsa.delay(userid)

    def _user_query(self, userid):
        return self.session.query(models.NipsaUser).filter_by(userid=userid)


def nipsa_factory(context, request):
    """Return a NipsaService instance for the passed context and request."""
    return NipsaService(request.db)

from h.models import User


class NipsaService:
    """A service which provides access to the state of "not-in-public-site-areas" (NIPSA) flags on userids."""

    def __init__(self, session, get_search_index):
        self.session = session
        self._get_search_index = get_search_index

        # Cache of all userids which have been flagged.
        self._flagged_userids = None

    def fetch_all_flagged_userids(self):
        """
        Fetch the userids of all shadowbanned / NIPSA'd users.

        The set of userids is cached to speed up subsequent `flagged_userids`
        and `is_flagged` calls in the same request.

        :rtype: set of unicode strings
        """
        if self._flagged_userids is not None:
            return self._flagged_userids

        # Filter using `is_` to match the index predicate for `User.nipsa`.
        query = self.session.query(User).filter(User.nipsa.is_(True))
        self._flagged_userids = {u.userid for u in query}

        return self._flagged_userids

    def is_flagged(self, userid):
        """Return whether the given userid is flagged as "NIPSA"."""

        # Use the cache if populated.
        if self._flagged_userids is not None:
            return userid in self._flagged_userids

        # Otherwise lookup the status for a single user, which is more efficient
        # than populating the cache if we are only looking up the NIPSA status
        # for a small number of users in a given task/request.
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
        if self._flagged_userids is not None:
            self._flagged_userids.add(user.userid)
        self._reindex_users_annotations(user, tag="NipsaService.flag")

    def unflag(self, user):
        """
        Remove the NIPSA flag for a user.

        If the user isn't NIPSA'd then nothing will happen (but a
        "remove_nipsa" message for the user will still be published to the
        queue).
        """
        user.nipsa = False
        if self._flagged_userids is not None:
            self._flagged_userids.remove(user.userid)
        self._reindex_users_annotations(user, tag="NipsaService.unflag")

    def clear(self):
        """Unload the cache of flagged userids, if populated."""
        self._flagged_userids = None

    def _reindex_users_annotations(self, user, tag):
        self._get_search_index().add_users_annotations(
            user.userid, tag=tag, force=True, schedule_in=30
        )


def nipsa_factory(_context, request):
    """Return a NipsaService instance for the passed context and request."""

    # NipsaService uses a search_index getter function rather than the search
    # index directly.
    #
    # This is because NipsaService is used in h.streamer where the search_index
    # service can't be constructed because there's no Elasticsearch connection.
    # Fortunately h.streamer doesn't call any of the NipsaService methods that
    # use search_index so as long as NipsaService is lazy about getting
    # search_index it won't crash the streamer.
    def get_search_index():
        return request.find_service(name="search_index")

    return NipsaService(request.db, get_search_index)

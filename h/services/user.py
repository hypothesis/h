import sqlalchemy as sa

from h.models import User, UserIdentity
from h.util.db import on_transaction_end
from h.util.user import split_user

UPDATE_PREFS_ALLOWED_KEYS = {"show_sidebar_tutorial"}


class UserNotActivated(Exception):
    """Tried to log in to an unactivated user account."""


class UserService:
    """A service for retrieving and performing common operations on users."""

    def __init__(self, default_authority, session):
        """
        Create a new user service.

        :param default_authority: the default authority for users
        :param session: the SQLAlchemy session object
        """
        self.default_authority = default_authority
        self.session = session

        # Local cache of fetched users.
        self._cache = {}

        # But don't allow the cache to persist after the session is closed.
        @on_transaction_end(session)
        def flush_cache():
            self._cache = {}

    def fetch(self, userid_or_username, authority=None):
        """
        Fetch a user by userid or by username and authority.

        Takes *either* a userid *or* a username and authority as arguments.
        For example::

          user_service.fetch('acct:foo@example.com')

        or::

          user_service.fetch('foo', 'example.com')

        :returns: a user instance, if found
        :raises InvalidUserId: If the userid cannot be parsed
        :rtype: h.models.User or None

        """
        if authority is not None:
            username = userid_or_username
        else:
            userid = userid_or_username
            parts = split_user(userid)
            username = parts["username"]
            authority = parts["domain"]

        # The cache is keyed by (username, authority) tuples.
        cache_key = (username, authority)

        if cache_key not in self._cache:
            self._cache[cache_key] = (
                self.session.query(User)
                .filter_by(username=username)
                .filter_by(authority=authority)
                .one_or_none()
            )

        return self._cache[cache_key]

    def fetch_all(self, userids):
        """
        Fetch a list of users by their userids.

        This function fetches users based on the list, adds them to the internal
        cache and then returns the list of users. This is especially useful
        when needing to access multiple user objects without loading them one-by-one.

        It will only attempt to load the users that aren't already cached.

        Userids that cannot be found will not be in the cache, so subsequent calls to `.fetch`
        are trying to load them again.

        :param userids: a list of userid strings.

        :returns: a list with the found user instances
        :rtype: list of h.models.User
        """
        if not userids:
            return []

        cache_keys = {}
        for userid in userids:
            val = split_user(userid)
            key = (val["username"], val["domain"])

            try:
                cache_keys[key] = userid
            except ValueError:
                continue

        userid_tuples = set(cache_keys.keys())
        missing_tuples = userid_tuples - set(self._cache.keys())
        missing_ids = [v for k, v in cache_keys.items() if k in missing_tuples]

        if missing_ids:
            users = self.session.query(User).filter(
                User.userid.in_(missing_ids)  # pylint:disable=no-member
            )  # pylint:disable=no-member
            for user in users:
                cache_key = (user.username, user.authority)
                self._cache[cache_key] = user

        return [v for k, v in self._cache.items() if k in cache_keys]

    def fetch_by_identity(self, provider, provider_unique_id):
        """
        Fetch a user by associated identity.

        :returns: a user instance, if found
        :rtype: h.models.User or None
        """

        identity = (
            self.session.query(UserIdentity)
            .filter_by(provider=provider, provider_unique_id=provider_unique_id)
            .one_or_none()
        )
        if identity:
            return identity.user
        return None

    def fetch_for_login(self, username_or_email):
        """
        Fetch a user by data provided in the login field.

        This searches for a user by username in the default authority, or by
        email in the default authority if `username_or_email` contains an "@"
        character.

        When fetching by an email address we use a case-insensitive query.

        :returns: A user object if a user was found, None otherwise.
        :rtype: h.models.User or NoneType
        :raises UserNotActivated: When the user is not activated.
        """
        filters = [(User.authority == self.default_authority)]
        if "@" in username_or_email:
            filters.append(sa.func.lower(User.email) == username_or_email.lower())
        else:
            filters.append(User.username == username_or_email)

        user = self.session.query(User).filter(*filters).one_or_none()

        if user is None:
            return None

        if not user.is_activated:
            raise UserNotActivated()

        return user

    @staticmethod
    def update_preferences(user, **kwargs):
        invalid_keys = set(kwargs.keys()) - UPDATE_PREFS_ALLOWED_KEYS
        if invalid_keys:
            keys = ", ".join(sorted(invalid_keys))
            raise TypeError(f"settings with keys {keys} are not allowed")

        if "show_sidebar_tutorial" in kwargs:
            user.sidebar_tutorial_dismissed = not kwargs["show_sidebar_tutorial"]


def user_service_factory(_context, request):
    """Return a UserService instance for the passed context and request."""
    return UserService(default_authority=request.default_authority, session=request.db)

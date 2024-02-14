from h import models, security
from h.util.db import lru_cache_in_transaction

PREFIX = "6879-"


class DeveloperTokenService:
    """A service for retrieving and performing common operations on developer tokens."""

    def __init__(self, session, user_svc):
        """
        Create a new developer token service.

        :param session: the SQLAlchemy session object
        """
        self.session = session
        self.user_svc = user_svc

        self._cached_fetch = lru_cache_in_transaction(self.session)(self._fetch)

    def fetch(self, userid):
        """
        Fetch a developer token by its userid.

        :param userid: The userid, typically of the currently authenticated user.
        :type userid: unicode

        :returns: a token instance, if found
        :rtype: h.models.Token or None
        """
        return self._cached_fetch(userid)

    def create(self, userid):
        """
        Create a developer token for the given userid.

        :param userid: The userid for which the developer token gets created.
        :type userid: unicode

        :returns: a token instance
        :rtype: h.models.Token
        """
        user = self.user_svc.fetch(userid)
        token = models.Token(user=user, value=self._generate_token())
        self.session.add(token)
        return token

    def regenerate(self, token):
        """
        Regenerates a developer token.

        The implementation changes the token value in-place, however when calling
        this method you should not rely on this implementation detail. You should
        use the return value of this method as the new token object.

        :param token: The token instance which needs to be regenerated.
        :type token: h.models.Token

        :returns: a regenerated token instance
        :rtype: h.models.Token
        """
        token.value = self._generate_token()
        return token

    def _fetch(self, userid):
        if userid is None:
            return None

        user = self.user_svc.fetch(userid)

        return (
            self.session.query(models.Token)
            .filter_by(user=user, authclient=None)
            .order_by(models.Token.created.desc())
            .one_or_none()
        )

    @staticmethod
    def _generate_token():
        return PREFIX + security.token_urlsafe()


def developer_token_service_factory(_context, request):
    return DeveloperTokenService(request.db, request.find_service(name="user"))

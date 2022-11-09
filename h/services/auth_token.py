from datetime import datetime
from typing import Optional

import newrelic.agent

from h.models import Token


class LongLivedToken:
    """
    A long-lived API token for a user.

    This is a wrapper class that wraps an `h.models.Token` but is not a
    sqlalchemy ORM class so it can be used after the request's db session has
    been committed or invalidated without getting `DetachedInstanceError`s.
    """

    def __init__(self, token):
        self.expires = token.expires
        self.userid = token.userid

        # Associates the userid with a given transaction/web request.
        newrelic.agent.add_custom_attribute("userid", self.userid)

    def is_valid(self):
        """Return ``True`` if this token is not expired, ``False`` if it is."""
        if self.expires is None:
            return True

        return datetime.utcnow() < self.expires


class AuthTokenService:
    def __init__(self, session):
        self._session = session
        self._validate_cache = {}

    def validate(self, token_str) -> Optional[LongLivedToken]:
        """
        Get a validated token from the token string or None.

        :param token_str: the token string
        """

        if token_str not in self._validate_cache:
            token = self.fetch(token_str)

            self._validate_cache[token_str] = LongLivedToken(token) if token else None

        if (
            long_lived_token := self._validate_cache[token_str]
        ) and long_lived_token.is_valid():
            return long_lived_token

        return None

    def fetch(self, token_str):
        """
        Fetch and return a token.

        This returns a ``h.models.Token`` in comparison to what ``validate``
        returns. Note that this method does not cache the loaded tokens, thus
        it will potentially run the same database query multiple times.

        :param token_str: the token string
        :type token_str: unicode

        :returns: the token object or ``None``
        """
        return self._session.query(Token).filter_by(value=token_str).one_or_none()

    @staticmethod
    def get_bearer_token(request):
        """
        Fetch the token (if any) associated with a request.

        :param request: the request object
        :returns: the auth token carried by the request, or None
        """
        try:
            header = request.headers["Authorization"]
        except KeyError:
            return None

        if not header.startswith("Bearer "):
            return None

        token = str(header[len("Bearer ") :]).strip()
        # If the token is empty at this point, it is clearly invalid and we
        # should reject it.
        if not token:
            return None

        return token


def auth_token_service_factory(_context, request):
    return AuthTokenService(request.db)

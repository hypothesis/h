from h import models
from h.auth.tokens import Token


class AuthTokenService:
    def __init__(self, session):
        self._session = session
        self._validate_cache = {}

    def validate(self, token_str):
        """
        Load and validate a token.

        This will return a token object implementing
        ``h.auth.interfaces.IAuthenticationToken``, or ``None`` when the token
        cannot be found, or is not valid.

        :param token_str: the token string
        :type token_str: unicode

        :returns: the token object, if found and valid, or ``None``.
        """

        if token_str in self._validate_cache:
            token = self._validate_cache[token_str]
            if token is not None and token.is_valid():
                return token
            return None

        token = self._fetch_auth_token(token_str)
        self._validate_cache[token_str] = token
        if token is not None and token.is_valid():
            return token
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
        return (
            self._session.query(models.Token).filter_by(value=token_str).one_or_none()
        )

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

    def _fetch_auth_token(self, token_str):
        token_model = self.fetch(token_str)
        if token_model is not None:
            token = Token(token_model)
            return token

        return None


def auth_token_service_factory(_context, request):
    return AuthTokenService(request.db)

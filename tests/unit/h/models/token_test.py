import datetime

from h.models import Token


class TestToken:
    def test_ttl_is_none_if_token_has_no_expires(self):
        assert Token().ttl is None

    def test_ttl_when_token_does_expire(self):
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # noqa: DTZ003
        token = Token(expires=expires)

        assert 0 < token.ttl < 3601

    def test_expired_is_false_if_expires_is_in_the_future(self):
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # noqa: DTZ003
        token = Token(expires=expires)

        assert not token.expired

    def test_expired_is_false_if_expires_is_none(self):
        token = Token(expires=None)

        assert not token.expired

    def test_expired_is_true_if_expires_is_in_the_past(self):
        expires = datetime.datetime.utcnow() - datetime.timedelta(hours=1)  # noqa: DTZ003
        token = Token(expires=expires)

        assert token.expired is True

    def test_refresh_token_expired_is_false_if_in_future(self):
        refresh_token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # noqa: DTZ003
        token = Token(refresh_token_expires=refresh_token_expires)

        assert not token.refresh_token_expired

    def test_refresh_token_expired_is_false_if_none(self):
        token = Token(refresh_token_expires=None)

        assert not token.refresh_token_expired

    def test_refresh_token_expired_is_true_if_in_past(self):
        refresh_token_expires = datetime.datetime.utcnow() - datetime.timedelta(hours=1)  # noqa: DTZ003
        token = Token(refresh_token_expires=refresh_token_expires)

        assert token.refresh_token_expired is True

    def test_repr(self, factories):
        token = factories.DeveloperToken()

        assert (
            repr(token)
            == f"Token(id={token.id!r}, user_id={token.user_id!r}, _authclient_id={token._authclient_id!r})"  # noqa: SLF001
        )

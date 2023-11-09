import pytest
from sqlalchemy.exc import IntegrityError

from h.models import AuthClient
from h.models.auth_client import GrantType


class TestAuthClient:
    def test_has_id(self, client):
        assert client.id

    def test_does_not_allow_empty_redirect_uri_for_authz_code_grant(
        self, factories, db_session
    ):
        client = factories.AuthClient.build(
            grant_type=GrantType.authorization_code, redirect_uri=None
        )
        db_session.add(client)

        with pytest.raises(IntegrityError):
            db_session.flush()

    @pytest.mark.parametrize(
        "grant_type",
        [GrantType.client_credentials, GrantType.jwt_bearer, GrantType.password],
    )
    def test_allows_empty_redirect_uri_for_other_grant(
        self, factories, db_session, grant_type
    ):
        client = factories.AuthClient.build(grant_type=grant_type, redirect_uri=None)
        db_session.add(client)
        db_session.flush()

    def test___repr__(self):
        client = AuthClient(id=123)

        assert repr(client) == "AuthClient(id=123)"

    @pytest.fixture
    def client(self, db_session):
        client = AuthClient(authority="example.com")
        db_session.add(client)
        db_session.flush()
        return client

import base64

import pytest

from h.models.auth_client import GrantType


@pytest.fixture
def authority():
    return "example.com"


@pytest.fixture
def user(_user_for_authority, authority):
    return _user_for_authority(authority)


@pytest.fixture
def auth_header(auth_header_for_authority, authority):
    return auth_header_for_authority(authority)


@pytest.fixture
def auth_header_for_authority(db_session, factories):
    def _make_headers(authority):
        auth_client = factories.ConfidentialAuthClient(
            authority=authority, grant_type=GrantType.client_credentials
        )
        db_session.commit()

        user_pass = f"{auth_client.id}:{auth_client.secret}".encode("utf-8")
        encoded = base64.standard_b64encode(user_pass).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    return _make_headers


@pytest.fixture
def token_auth_header(db_session, factories, user):
    token = factories.DeveloperToken(user=user)
    db_session.add(token)
    db_session.commit()

    return {"Authorization": f"Bearer {token.value}"}


@pytest.fixture
def _user_for_authority(db_session, factories):
    def _make_user(authority):
        user = factories.User(authority=authority)
        db_session.commit()
        return user

    return _make_user

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import base64


from h.models.auth_client import GrantType

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestCreateUser(object):

    def test_it_returns_http_200_when_successful(self, app, auth_client_header, user_payload):
        res = app.post_json("/api/users", user_payload, headers=auth_client_header)

        assert res.status_code == 200

    def test_it_returns_404_if_missing_auth_client(self, app, user_payload):
        # FIXME: This should return a 403; our exception views squash it into a 404
        res = app.post_json("/api/users", user_payload, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_403_if_missing_auth_client(self, app, user_payload):
        res = app.post_json("/api/users", user_payload, expect_errors=True)

        assert res.status_code == 403

    def test_it_returns_400_if_invalid_payload(self, app, user_payload, auth_client_header):
        del user_payload["username"]

        res = app.post_json("/api/users", user_payload, headers=auth_client_header, expect_errors=True)

        assert res.status_code == 400

    def test_it_returns_409_if_user_conflict(self, app, user_payload, auth_client_header, user):
        # user fixture creates user with conflicting username/authority combo
        res = app.post_json("/api/users", user_payload, headers=auth_client_header, expect_errors=True)

        assert res.status_code == 409


@pytest.fixture
def user_payload():
    return {
        "username": "filip",
        "email": "filip@example.com",
        "authority": "example.com"
    }


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.ConfidentialAuthClient(authority='example.com',
                                                   grant_type=GrantType.client_credentials)
    db_session.commit()
    return auth_client


@pytest.fixture
def auth_client_header(auth_client):
    user_pass = "{client_id}:{secret}".format(client_id=auth_client.id, secret=auth_client.secret)
    encoded = base64.standard_b64encode(user_pass.encode('utf-8'))
    return {native_str('Authorization'): native_str("Basic {creds}".format(creds=encoded.decode('ascii')))}


@pytest.fixture
def user(db_session, factories):
    user = factories.User(username="filip", authority="example.com")
    db_session.commit()
    return user

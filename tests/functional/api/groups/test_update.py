# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import base64

from h.models.auth_client import GrantType

native_str = str


@pytest.mark.functional
class TestUpdateGroup(object):
    def test_it_returns_http_200_with_valid_payload_and_user_token(
        self, app, token_auth_header, first_party_group
    ):
        group = {"name": "Rename My Group"}
        res = app.patch_json(
            "/api/groups/{id}".format(id=first_party_group.pubid),
            group,
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "Rename My Group"
        assert res.json_body["groupid"] is None

    def test_it_does_not_update_group_if_empty_payload_and_user_token(
        self, app, token_auth_header, first_party_group
    ):
        payload = {}
        res = app.patch_json(
            "/api/groups/{id}".format(id=first_party_group.pubid),
            payload,
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "My First Group"
        assert res.json_body["groupid"] is None

    def test_it_ignores_non_whitelisted_fields_in_payload_and_user_token(
        self, app, token_auth_header, first_party_group
    ):
        group = {
            "id": "fbdzzz",
            "name": "My Group",
            "organization": "foobar",
            "joinable_by": "whoever",
        }
        res = app.patch_json(
            "/api/groups/{id}".format(id=first_party_group.pubid),
            group,
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["id"] != group["id"]
        assert res.json_body["organization"] is None

    def test_it_returns_http_400_with_invalid_payload_and_user_token(
        self, app, token_auth_header, first_party_group
    ):
        group = {
            "name": "Oooopoooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
        }

        res = app.patch_json(
            "/api/groups/{id}".format(id=first_party_group.pubid),
            group,
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority_and_user_token(
        self, app, token_auth_header, first_party_group
    ):
        group = {"groupid": "3434kjkjk"}
        res = app.patch_json(
            "/api/groups/{id}".format(id=first_party_group.pubid),
            group,
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_404_if_no_authenticated_user(self, app, first_party_group):
        group = {"name": "My Group"}
        res = app.patch_json(
            "/api/groups/{id}".format(id=first_party_group.pubid),
            group,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_if_token_user_unauthorized(
        self, app, token_auth_header, factories, db_session
    ):
        # Not created by user represented by token_auth_header
        group = factories.Group()
        db_session.commit()

        group_payload = {"name": "My Group"}
        res = app.patch_json(
            "/api/groups/{id}".format(id=group.pubid),
            group_payload,
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_allows_auth_client_with_valid_forwarded_user(
        self, app, auth_client_header, third_party_user, factories, db_session
    ):
        group = factories.Group(
            creator=third_party_user, authority=third_party_user.authority
        )
        db_session.commit()

        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group_payload = {"name": "My Group"}

        path = "/api/groups/{id}".format(id=group.pubid)
        res = app.patch_json(path, group_payload, headers=headers)

        assert res.status_code == 200
        assert res.json_body["name"] == "My Group"

    def test_it_allows_auth_client_with_matching_authority(
        self, app, auth_client_header, third_party_user, factories, db_session
    ):
        group = factories.Group(
            creator=third_party_user, authority=third_party_user.authority
        )
        db_session.commit()

        group_payload = {"name": "My Group"}

        path = "/api/groups/{id}".format(id=group.pubid)
        res = app.patch_json(path, group_payload, headers=auth_client_header)

        assert res.status_code == 200
        assert res.json_body["name"] == "My Group"

    def test_it_does_not_allow_auth_client_with_mismatched_authority(
        self, app, auth_client_header, factories, db_session
    ):
        group = factories.Group(authority="rando.biz")
        db_session.commit()

        group_payload = {"name": "My Group"}

        path = "/api/groups/{id}".format(id=group.pubid)
        res = app.patch_json(
            path, group_payload, headers=auth_client_header, expect_errors=True
        )

        assert res.status_code == 404

    def test_it_allows_groupid_from_auth_client_with_forwarded_user(
        self, app, auth_client_header, third_party_user, factories, db_session
    ):
        group = factories.Group(
            creator=third_party_user, authority=third_party_user.authority
        )
        db_session.commit()

        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group_payload = {
            "name": "My Group",
            "groupid": "group:333vcdfkj~@thirdparty.com",
        }

        path = "/api/groups/{id}".format(id=group.pubid)
        res = app.patch_json(path, group_payload, headers=headers)

        assert res.status_code == 200
        assert "groupid" in res.json_body
        assert res.json_body["groupid"] == "group:{groupid}@thirdparty.com".format(
            groupid="333vcdfkj~"
        )

    def test_it_returns_HTTP_Conflict_if_groupid_is_duplicate(
        self, app, auth_client_header, third_party_user, factories, db_session
    ):
        group1 = factories.Group(
            creator=third_party_user,
            authority=third_party_user.authority,
            groupid="group:one@thirdparty.com",
        )
        group2 = factories.Group(
            creator=third_party_user,
            authority=third_party_user.authority,
            groupid="group:two@thirdparty.com",
        )
        db_session.commit()

        headers = auth_client_header
        headers[native_str("X-Forwarded-User")] = native_str(third_party_user.userid)
        group_payload = {"groupid": "group:one@thirdparty.com"}

        # Attempting to set group2's `groupid` to one already taken by group1
        path = "/api/groups/{id}".format(id=group2.pubid)
        res = app.patch_json(path, group_payload, headers=headers, expect_errors=True)

        assert group1.groupid in res.json_body["reason"]
        assert res.status_code == 409


@pytest.fixture
def first_party_user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def first_party_group(db_session, factories, first_party_user):
    group = factories.Group(
        name="My First Group",
        description="Original description",
        creator=first_party_user,
        authority=first_party_user.authority,
    )
    db_session.commit()
    return group


@pytest.fixture
def user_with_token(db_session, factories, first_party_user):
    token = factories.DeveloperToken(userid=first_party_user.userid)
    db_session.add(token)
    db_session.commit()
    return (first_party_user, token)


@pytest.fixture
def token_auth_header(user_with_token):
    user, token = user_with_token
    return {native_str("Authorization"): native_str("Bearer {}".format(token.value))}


@pytest.fixture
def third_party_user(factories, db_session):
    user = factories.User(authority="thirdparty.com")
    db_session.commit()
    return user


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.ConfidentialAuthClient(
        authority="thirdparty.com", grant_type=GrantType.client_credentials
    )
    db_session.commit()
    return auth_client


@pytest.fixture
def auth_client_header(auth_client):
    user_pass = "{client_id}:{secret}".format(
        client_id=auth_client.id, secret=auth_client.secret
    )
    encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
    return {
        native_str("Authorization"): native_str(
            "Basic {creds}".format(creds=encoded.decode("ascii"))
        )
    }

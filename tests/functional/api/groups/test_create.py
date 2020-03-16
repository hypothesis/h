# -*- coding: utf-8 -*-

import pytest


class TestCreateGroup:
    def test_it_returns_http_200_with_valid_payload(self, app, token_auth_header):
        res = app.post_json(
            "/api/groups", {"name": "My Group"}, headers=token_auth_header
        )

        assert res.status_code == 200

    def test_it_ignores_non_whitelisted_fields_in_payload(self, app, token_auth_header):
        res = app.post_json(
            "/api/groups",
            {"name": "My Group", "organization": "foobar", "joinable_by": "whoever"},
            headers=token_auth_header,
        )

        assert res.status_code == 200

    def test_it_returns_http_400_with_invalid_payload(self, app, token_auth_header):

        res = app.post_json(
            "/api/groups", {}, headers=token_auth_header, expect_errors=True
        )

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority(
        self, app, token_auth_header
    ):
        res = app.post_json(
            "/api/groups",
            {"name": "My Group", "groupid": "3434kjkjk"},
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_404_if_no_authenticated_user(self, app, auth_header):
        # FIXME: This should return a 403
        res = app.post_json(
            "/api/groups", {"name": "My Group"}, headers=auth_header, expect_errors=True
        )

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_http_403_if_no_authenticated_user(self, app, auth_header):
        res = app.post_json(
            "/api/groups", {"name": "My Group"}, headers=auth_header, expect_errors=True
        )

        assert res.status_code == 403

    def test_it_allows_auth_client_with_forwarded_user(self, app, auth_header, user):
        headers = auth_header
        headers["X-Forwarded-User"] = user.userid

        res = app.post_json("/api/groups", {"name": "My Group"}, headers=headers)

        assert res.status_code == 200

    def test_it_allows_groupdid_from_auth_client_with_forwarded_user(
        self, app, auth_headers_3rd_party, user_3rd_party
    ):
        res = app.post_json(
            "/api/groups",
            {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.example.com"},
            headers=auth_headers_3rd_party,
        )
        data = res.json

        assert res.status_code == 200
        assert "groupid" in data
        assert data["groupid"] == "group:333vcdfkj~@thirdparty.example.com"

    def test_it_returns_HTTP_Conflict_if_groupid_is_duplicate(
        self, app, auth_headers_3rd_party, user_3rd_party
    ):
        body = {
            "name": "My Group",
            "groupid": "group:333vcdfkj~@thirdparty.example.com",
        }

        app.post_json("/api/groups", body, headers=auth_headers_3rd_party)
        res = app.post_json(
            "/api/groups", body, headers=auth_headers_3rd_party, expect_errors=True
        )

        assert res.status_code == 409

    def test_it_returns_http_404_with_invalid_forwarded_user_format(
        self, app, auth_header
    ):
        # FIXME: This should return a 403
        headers = auth_header
        headers["X-Forwarded-User"] = "floopflarp"

        res = app.post_json("/api/groups", {}, headers=headers, expect_errors=True)

        assert res.status_code == 404

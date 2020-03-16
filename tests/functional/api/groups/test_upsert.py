# -*- coding: utf-8 -*-


class TestUpsertGroupUpdate:
    def test_it_returns_http_404_if_no_authenticated_user(self, app, group):
        res = app.put_json(
            f"/api/groups/{group.pubid}", {"name": "My Group"}, expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_200_with_valid_payload_and_user_token(
        self, app, token_auth_header, group
    ):
        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "Rename My Group"},
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "Rename My Group"
        assert res.json_body["groupid"] is None

    def test_it_ignores_non_whitelisted_fields_in_payload(
        self, app, token_auth_header, group
    ):
        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "Rename Me", "organization": "foobar", "joinable_by": "whoever"},
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["organization"] is None

    def test_it_returns_http_400_with_invalid_payload(
        self, app, token_auth_header, group
    ):
        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {},
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority(
        self, app, token_auth_header, group
    ):
        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "Egghead", "groupid": "3434kjkjk"},
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_404_if_token_user_unauthorized(
        self, app, token_auth_header, factories, db_session
    ):
        # Not created by user represented by token_auth_header
        group = factories.Group()
        db_session.commit()

        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group"},
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_allows_auth_client_with_valid_forwarded_user(
        self, app, auth_headers_3rd_party, user_3rd_party, factories, db_session
    ):
        group = factories.Group(
            creator=user_3rd_party, authority=user_3rd_party.authority
        )
        db_session.commit()

        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group"},
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "My Group"

    def test_it_returns_404_if_forwarded_user_is_not_authorized_to_update(
        self, app, auth_header, user_3rd_party, factories, db_session
    ):
        # Not created by `user`
        group = factories.Group(authority=user_3rd_party.authority)
        db_session.commit()

        headers = auth_header
        headers["X-Forwarded-User"] = user_3rd_party.userid

        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group"},
            headers=headers,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_allows_groupid_from_auth_client_with_forwarded_user(
        self, app, auth_headers_3rd_party, user_3rd_party, factories, db_session
    ):
        group = factories.Group(
            creator=user_3rd_party, authority=user_3rd_party.authority
        )
        db_session.commit()

        res = app.put_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.example.com"},
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert "groupid" in res.json_body
        assert res.json_body["groupid"] == "group:333vcdfkj~@thirdparty.example.com"

    def test_it_supersedes_groupid_with_value_in_payload(
        self, app, auth_headers_3rd_party, user_3rd_party, factories, db_session
    ):
        # In this test, the ``groupid`` in the path param is different than that
        # indicated in the payload. This allows a caller to change the ``groupid``
        group = factories.Group(
            creator=user_3rd_party,
            authority=user_3rd_party.authority,
            authority_provided_id="doodad",
        )
        db_session.commit()

        res = app.put_json(
            f"/api/groups/{group.groupid}",
            {"name": "My Group", "groupid": "group:ice-cream@thirdparty.example.com"},
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert "groupid" in res.json_body
        assert res.json_body["groupid"] == "group:ice-cream@thirdparty.example.com"

    def test_it_returns_HTTP_Conflict_if_groupid_is_duplicate(
        self, app, auth_headers_3rd_party, user_3rd_party, factories, db_session
    ):
        group1 = factories.Group(
            creator=user_3rd_party,
            authority=user_3rd_party.authority,
            groupid="group:one@thirdparty.example.com",
        )
        group2 = factories.Group(
            creator=user_3rd_party,
            authority=user_3rd_party.authority,
            groupid="group:two@thirdparty.example.com",
        )
        db_session.commit()

        # Attempting to set group2's `groupid` to one already taken by group1
        res = app.put_json(
            f"/api/groups/{group2.groupid}",
            {"name": "Whatnot", "groupid": "group:one@thirdparty.example.com"},
            headers=auth_headers_3rd_party,
            expect_errors=True,
        )

        assert group1.groupid in res.json_body["reason"]
        assert res.status_code == 409


class TestUpsertGroupCreate:
    def test_it_allows_auth_client_with_forwarded_user(
        self, app, auth_headers_3rd_party, user_3rd_party
    ):
        res = app.put_json(
            "/api/groups/somepubid",
            {
                "name": "My Group",
                "groupid": f"group:foothold@{user_3rd_party.authority}",
            },
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "My Group"
        assert res.json_body["groupid"] == f"group:foothold@{user_3rd_party.authority}"

    def test_it_allows_user_with_token(self, app, token_auth_header):
        res = app.put_json(
            "/api/groups/randompubid",
            {"name": "This is my group"},
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "This is my group"
        assert res.json_body["groupid"] is None

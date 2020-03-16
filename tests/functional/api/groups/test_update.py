# -*- coding: utf-8 -*-


class TestUpdateGroup:
    def test_it_returns_http_200_with_valid_payload_and_user_token(
        self, app, token_auth_header, group
    ):
        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {"name": "Rename My Group"},
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "Rename My Group"
        assert res.json_body["groupid"] is None

    def test_it_does_not_update_group_if_empty_payload_and_user_token(
        self, app, token_auth_header, group
    ):

        res = app.patch_json(
            f"/api/groups/{group.pubid}", {}, headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "My First Group"
        assert res.json_body["groupid"] is None

    def test_it_ignores_non_whitelisted_fields_in_payload_and_user_token(
        self, app, token_auth_header, group
    ):
        new_id = "fbdzzz"

        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {
                "id": new_id,
                "name": "My Group",
                "organization": "foobar",
                "joinable_by": "whoever",
            },
            headers=token_auth_header,
        )

        assert res.status_code == 200
        assert res.json_body["id"] != new_id
        assert res.json_body["organization"] is None

    def test_it_returns_http_400_with_invalid_payload_and_user_token(
        self, app, token_auth_header, group
    ):
        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {
                "name": "Oooopoooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
            },
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_400_if_groupid_set_on_default_authority_and_user_token(
        self, app, token_auth_header, group
    ):
        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {"groupid": "3434kjkjk"},
            headers=token_auth_header,
            expect_errors=True,
        )

        assert res.status_code == 400

    def test_it_returns_http_404_if_no_authenticated_user(self, app, group):
        res = app.patch_json(
            f"/api/groups/{group.pubid}", {"name": "My Group"}, expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_if_token_user_unauthorized(
        self, app, token_auth_header, factories, db_session
    ):
        # Not created by user represented by token_auth_header
        group = factories.Group()
        db_session.commit()

        res = app.patch_json(
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

        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group"},
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "My Group"

    def test_it_allows_auth_client_with_matching_authority(
        self, app, auth_headers_3rd_party, user_3rd_party, factories, db_session
    ):
        group = factories.Group(
            creator=user_3rd_party, authority=user_3rd_party.authority
        )
        db_session.commit()

        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group"},
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert res.json_body["name"] == "My Group"

    def test_it_does_not_allow_auth_client_with_mismatched_authority(
        self, app, auth_header, factories, db_session
    ):
        group = factories.Group(authority="rando.biz")
        db_session.commit()

        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group"},
            headers=auth_header,
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

        res = app.patch_json(
            f"/api/groups/{group.pubid}",
            {"name": "My Group", "groupid": "group:333vcdfkj~@thirdparty.example.com"},
            headers=auth_headers_3rd_party,
        )

        assert res.status_code == 200
        assert "groupid" in res.json_body
        assert res.json_body["groupid"] == "group:333vcdfkj~@thirdparty.example.com"

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
        res = app.patch_json(
            f"/api/groups/{group2.pubid}",
            {"groupid": "group:one@thirdparty.example.com"},
            headers=auth_headers_3rd_party,
            expect_errors=True,
        )

        assert group1.groupid in res.json_body["reason"]
        assert res.status_code == 409

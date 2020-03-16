# -*- coding: utf-8 -*-


class TestReadGroups:
    # TODO: In subsequent versions of the API, this should really be a group
    # search endpoint and should have its own functional test module

    def test_it_returns_world_group(self, app):
        # world group is auto-added in tests
        res = app.get("/api/groups")

        assert res.status_code == 200
        assert res.json[0]["id"] == "__world__"

    def test_it_returns_private_groups_along_with_world_groups(
        self, app, factories, db_session, user, token_auth_header
    ):

        group1 = factories.Group(creator=user)
        group2 = factories.Group(creator=user)
        db_session.commit()

        res = app.get("/api/groups", headers=token_auth_header)

        groupids = [group["id"] for group in res.json]
        assert "__world__" in groupids
        assert group1.pubid in groupids
        assert group2.pubid in groupids

    def test_it_overrides_authority_param_with_user_authority(
        self, app, factories, db_session, user, token_auth_header
    ):
        # This group will be created with the user's authority
        group1 = factories.Group(creator=user)
        db_session.commit()

        res = app.get("/api/groups?authority=whatever.com", headers=token_auth_header)

        groupids = [group["id"] for group in res.json]
        # It still returns the groups from the user's authority
        assert group1.pubid in groupids

    def test_it_expands_scope_if_requested(self, app):
        res = app.get("/api/groups?expand=scopes")

        assert res.status_code == 200
        assert "scopes" in res.json[0]


class TestReadGroup:
    def test_it_returns_http_200_for_world_readable_group_pubid(
        self, app, factories, db_session
    ):
        group = factories.OpenGroup()
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}")

        assert res.status_code == 200

        data = res.json
        assert "id" in data

    def test_it_returns_http_200_for_world_readable_groupid(
        self, app, factories, db_session
    ):
        factories.OpenGroup(authority_provided_id="foo", authority="bar.com")
        db_session.commit()
        res = app.get("/api/groups/group:foo@bar.com")

        assert res.status_code == 200

    def test_it_returns_http_404_for_private_group_no_authentication(
        self, app, factories, db_session
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}", expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_http_200_for_private_group_with_creator_authentication(
        self, app, user, token_auth_header, factories, db_session
    ):
        group = factories.Group(creator=user)
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}", headers=token_auth_header)

        assert res.status_code == 200

    def test_it_returns_http_200_for_private_group_with_member_authentication(
        self, app, user, token_auth_header, factories, db_session
    ):
        group = factories.Group()
        group.members.append(user)
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}", headers=token_auth_header)

        assert res.status_code == 200

    def test_it_returns_http_404_for_private_group_if_token_user_not_creator(
        self, app, token_auth_header, factories, db_session
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(
            f"/api/groups/{group.pubid}", headers=token_auth_header, expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_200_for_private_group_with_auth_client_matching_authority(
        self, app, auth_header, factories, db_session, group
    ):
        db_session.commit()

        res = app.get(f"/api/groups/{group.pubid}", headers=auth_header)

        assert res.status_code == 200

    def test_it_returns_http_404_for_private_group_with_auth_client_mismatched_authority(
        self, app, auth_header, factories, db_session
    ):
        group = factories.Group(authority="somewhere-else.com")
        db_session.commit()

        res = app.get(
            f"/api/groups/{group.pubid}", headers=auth_header, expect_errors=True,
        )

        assert res.status_code == 404

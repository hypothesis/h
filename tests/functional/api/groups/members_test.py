import base64
import logging

import pytest
from sqlalchemy import select

from h.models import GroupMembership, GroupMembershipRoles, Token
from h.models.auth_client import AuthClient, GrantType


class TestListMembersLegacy:
    def test_it_returns_list_of_members_for_restricted_group_without_authn(
        self, app, factories, db_session, caplog
    ):
        group = factories.RestrictedGroup(
            memberships=[
                GroupMembership(user=user)
                for user in factories.User.create_batch(size=3)
            ]
        )
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers={"User-Agent": "test_user_agent", "Referer": "test_referer"},
        )

        assert caplog.messages == [
            f"list_members_legacy() was called. User-Agent: test_user_agent, Referer: test_referer, pubid: {group.pubid}"
        ]
        assert res.status_code == 200
        assert res.json == [
            {
                "authority": membership.group.authority,
                "userid": membership.user.userid,
                "username": membership.user.username,
                "display_name": membership.user.display_name,
                "roles": membership.roles,
                "actions": [],
            }
            for membership in sorted(
                group.memberships, key=lambda membership: membership.user.username
            )
        ]

    def test_it_returns_list_of_members_if_user_has_access_to_private_group(
        self, app, factories, db_session
    ):
        group = factories.Group()
        user, other_user = factories.User.create_batch(size=2)
        token = factories.DeveloperToken(user=user)
        group.memberships.extend(
            [GroupMembership(user=user), GroupMembership(user=other_user)]
        )
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers=token_authorization_header(token),
        )

        assert res.status_code == 200
        assert res.json == sorted(
            [
                {
                    "authority": group.authority,
                    "userid": user.userid,
                    "username": user.username,
                    "display_name": user.display_name,
                    "roles": [GroupMembershipRoles.MEMBER],
                    "actions": ["delete"],
                },
                {
                    "authority": group.authority,
                    "userid": other_user.userid,
                    "username": other_user.username,
                    "display_name": other_user.display_name,
                    "roles": [GroupMembershipRoles.MEMBER],
                    "actions": [],
                },
            ],
            key=lambda membership: membership["username"],
        )

    def test_it_returns_404_if_user_does_not_have_read_access_to_group(
        self, app, db_session, factories
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            headers=token_authorization_header(factories.DeveloperToken()),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_empty_list_if_no_members_in_group(self, app):
        res = app.get("/api/groups/__world__/members")

        assert res.json == []


class TestListMembers:
    def test_it_returns_list_of_members_for_restricted_group_without_auth(
        self, app, factories, db_session
    ):
        group = factories.RestrictedGroup(
            memberships=[
                GroupMembership(user=user)
                for user in factories.User.create_batch(size=4)
            ]
        )
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            params={"page[offset]": 1, "page[limit]": 2},
            headers={"User-Agent": "test_user_agent", "Referer": "test_referer"},
        )

        assert res.status_code == 200
        assert res.json == {
            "meta": {"page": {"total": 4}},
            "data": [
                {
                    "authority": membership.group.authority,
                    "userid": membership.user.userid,
                    "username": membership.user.username,
                    "display_name": membership.user.display_name,
                    "roles": membership.roles,
                    "actions": [],
                }
                for membership in sorted(
                    group.memberships, key=lambda membership: membership.user.username
                )[1:3]
            ],
        }

    def test_it_returns_list_of_members_if_user_has_access_to_private_group(
        self, app, factories, db_session
    ):
        group = factories.Group()
        user, other_user = factories.User.create_batch(size=2)
        token = factories.DeveloperToken(user=user)
        group.memberships.extend(
            [GroupMembership(user=user), GroupMembership(user=other_user)]
        )
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            params={"page[offset]": 0},
            headers=token_authorization_header(token),
        )

        assert res.status_code == 200
        assert res.json == {
            "meta": {"page": {"total": 2}},
            "data": sorted(
                [
                    {
                        "authority": group.authority,
                        "userid": user.userid,
                        "username": user.username,
                        "display_name": user.display_name,
                        "roles": [GroupMembershipRoles.MEMBER],
                        "actions": ["delete"],
                    },
                    {
                        "authority": group.authority,
                        "userid": other_user.userid,
                        "username": other_user.username,
                        "display_name": other_user.display_name,
                        "roles": [GroupMembershipRoles.MEMBER],
                        "actions": [],
                    },
                ],
                key=lambda membership: membership["username"],
            ),
        }

    def test_it_returns_404_if_user_does_not_have_read_access_to_group(
        self, app, db_session, factories
    ):
        group = factories.Group()
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            params={"page[offset]": 0},
            headers=token_authorization_header(factories.DeveloperToken()),
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_empty_list_if_no_members_in_group(self, app):
        res = app.get(
            "/api/groups/__world__/members",
            params={"page[offset]": 0},
        )

        assert res.json == {"meta": {"page": {"total": 0}}, "data": []}

    def test_it_returns_an_error_if_offset_and_limit_are_invalid(
        self, app, db_session, factories
    ):
        group = factories.Group()
        user = factories.User()
        token = factories.DeveloperToken(user=user)
        group.memberships.extend([GroupMembership(user=user)])
        db_session.commit()

        res = app.get(
            "/api/groups/{pubid}/members".format(pubid=group.pubid),
            params={"page[offset]": -1, "page[limit]": 0},
            headers=token_authorization_header(token),
            expect_errors=True,
        )

        assert res.status_code == 400
        assert res.json == {
            "reason": "page[offset]: -1 is less than minimum value 0\npage[limit]: 0 is less than minimum value 1",
            "status": "failure",
        }


class TestAddMember:
    def test_it(self, do_request, group, user):
        do_request()

        assert user in group.members

    def test_it_does_nothing_if_the_user_is_already_a_member_of_the_group(
        self, do_request, group, user
    ):
        group.memberships.append(GroupMembership(user=user))

        do_request()

        assert user in group.members

    def test_it_errors_if_the_pubid_is_unknown(self, do_request):
        do_request(pubid="UNKNOWN_PUBID", status=404)

    def test_it_errors_if_the_userid_is_unknown(self, do_request, authclient):
        do_request(userid="acct:UNKOWN_USERNAME@{authclient.authority}", status=404)

    def test_it_errors_if_the_userid_is_invalid(self, do_request):
        do_request(userid="INVALID_USERID", status=404)

    def test_it_errors_if_the_request_isnt_authenticated(self, do_request, headers):
        del headers["Authorization"]

        do_request(status=404)

    def test_it_errors_if_the_request_has_token_authentication(
        self, do_request, factories, user, headers
    ):
        token = factories.DeveloperToken(user=user)
        headers.update(token_authorization_header(token))

        do_request(status=404)

    def test_it_errors_if_the_groups_authority_doesnt_match(
        self, do_request, factories
    ):
        group = factories.Group(authority="other")

        do_request(pubid=group.pubid, status=404)

    def test_it_errors_if_the_users_authority_doesnt_match(self, do_request, factories):
        user = factories.User(authority="other")

        do_request(userid=user.userid, status=404)

    def test_it_errors_if_the_groups_and_users_authorities_both_dont_match(
        self, do_request, factories
    ):
        # The user and group have the same authority but it is different from
        # the authclient's authority.
        group = factories.Group(authority="other")
        user = factories.User(authority=group.authority)

        do_request(pubid=group.pubid, userid=user.userid, status=404)

    def test_it_ignores_forwarded_users(
        self, do_request, factories, authclient, headers, user, group
    ):
        forwarded_user = factories.User(authority=authclient.authority)
        headers["X-Forwarded-User"] = forwarded_user.userid

        do_request()

        # It has added the user from the URL to the group.
        assert user in group.members
        # It has *not* added the user from the X-Forwarded-User header to the group.
        assert forwarded_user not in group.members

    def test_me_alias_with_forwarded_user(
        self, do_request, factories, authclient, headers, group
    ):
        forwarded_user = factories.User(authority=authclient.authority)
        headers["X-Forwarded-User"] = forwarded_user.userid

        do_request(userid="me")

        # If the "me" alias is used with an X-Forwarded-User header it should
        # add the forwarded user to the group.
        assert forwarded_user in group.members

    def test_me_alias_with_forwarded_user_with_wrong_authority(
        self, do_request, factories, headers
    ):
        forwarded_user = factories.User(authority="other")
        headers["X-Forwarded-User"] = forwarded_user.userid

        do_request(userid="me", status=404)

    def test_me_alias_without_forwarded_user(self, do_request):
        do_request(userid="me", status=404)

    @pytest.fixture
    def do_request(self, db_session, app, group, user, headers):
        def do_request(pubid=group.pubid, userid=user.userid, status=204):
            db_session.commit()
            return app.post_json(
                f"/api/groups/{pubid}/members/{userid}", headers=headers, status=status
            )

        return do_request

    @pytest.fixture
    def authclient(self, factories):
        return factories.ConfidentialAuthClient(
            authority="thirdparty.com", grant_type=GrantType.client_credentials
        )

    @pytest.fixture
    def headers(self, authclient):
        user_pass = "{client_id}:{secret}".format(
            client_id=authclient.id, secret=authclient.secret
        )
        encoded = base64.standard_b64encode(user_pass.encode("utf-8"))
        return {"Authorization": "Basic {creds}".format(creds=encoded.decode("ascii"))}

    @pytest.fixture
    def group(self, authclient, factories):
        return factories.Group(authority=authclient.authority)

    @pytest.fixture
    def user(self, authclient, factories):
        return factories.User(authority=authclient.authority)


class TestRemoveMember:
    @pytest.mark.parametrize(
        "authenticated_users_role,target_users_role,expect_success",
        [
            # Only owners can remove other owners.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.OWNER, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.OWNER, False),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.OWNER, False),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.OWNER, False),
            # Only owners can remove admins.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.ADMIN, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.ADMIN, False),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.ADMIN, False),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.ADMIN, False),
            # Owners and admins can remove moderators.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.MODERATOR, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.MODERATOR, True),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.MODERATOR, False),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.MODERATOR, False),
            # Owners, admins and moderators can remove members.
            (GroupMembershipRoles.OWNER, GroupMembershipRoles.MEMBER, True),
            (GroupMembershipRoles.ADMIN, GroupMembershipRoles.MEMBER, True),
            (GroupMembershipRoles.MODERATOR, GroupMembershipRoles.MEMBER, True),
            (GroupMembershipRoles.MEMBER, GroupMembershipRoles.MEMBER, False),
            # Non-members can't remove anyone.
            (None, GroupMembershipRoles.OWNER, False),
            (None, GroupMembershipRoles.ADMIN, False),
            (None, GroupMembershipRoles.MEMBER, False),
            (None, GroupMembershipRoles.MODERATOR, False),
        ],
    )
    def test_it(
        self,
        app,
        db_session,
        factories,
        authenticated_users_role,
        target_users_role,
        expect_success,
    ):
        group, other_group = factories.Group.create_batch(size=2)
        # The target user who we will remove from the group.
        target_user = factories.User()
        db_session.add(
            GroupMembership(group=group, user=target_user, roles=[target_users_role])
        )
        # Another user who is a member of the group.
        # This user should *not* be removed from the group.
        other_user = factories.User()
        db_session.add(GroupMembership(user=other_user, group=group))
        # Make the target user a member of another group as well.
        # The target user should *not* be removed from this group.
        db_session.add(GroupMembership(user=target_user, group=other_group))
        # The authenticated user who will make the request.
        authenticated_user = factories.User()
        if authenticated_users_role:
            db_session.add(
                GroupMembership(
                    group=group,
                    user=authenticated_user,
                    roles=[authenticated_users_role],
                )
            )
        token = factories.DeveloperToken(user=authenticated_user)
        db_session.commit()

        app.delete(
            f"/api/groups/{group.pubid}/members/{target_user.userid}",
            headers=token_authorization_header(token),
            status=204 if expect_success else 404,
        )

        if expect_success:
            assert target_user not in group.members
        else:
            assert target_user in group.members
        assert target_user in other_group.members
        assert other_user in group.members

    @pytest.mark.parametrize(
        "role",
        [
            GroupMembershipRoles.OWNER,
            GroupMembershipRoles.ADMIN,
            GroupMembershipRoles.MODERATOR,
            GroupMembershipRoles.MEMBER,
        ],
    )
    def test_any_member_can_remove_themselves_from_a_group(
        self, app, db_session, factories, role
    ):
        group, other_group = factories.Group.create_batch(size=2)
        user, other_user = factories.User.create_batch(size=2)
        db_session.add_all(
            [
                GroupMembership(group=group, user=user, roles=[role]),
                GroupMembership(group=other_group, user=user),
                GroupMembership(group=group, user=other_user),
            ]
        )
        token = factories.DeveloperToken(user=user)
        db_session.commit()

        app.delete(
            f"/api/groups/{group.pubid}/members/{user.userid}",
            headers=token_authorization_header(token),
        )

        assert user not in group.members
        assert user in other_group.members
        assert other_user in group.members

    @pytest.mark.parametrize(
        "role",
        [
            GroupMembershipRoles.OWNER,
            GroupMembershipRoles.ADMIN,
            GroupMembershipRoles.MODERATOR,
            GroupMembershipRoles.MEMBER,
        ],
    )
    def test_unauthenticated_requests_cant_remove_anyone_from_groups(
        self, app, db_session, factories, role
    ):
        group = factories.Group()
        user = factories.User()
        db_session.add(GroupMembership(group=group, user=user, roles=[role]))
        db_session.commit()

        app.delete(f"/api/groups/{group.pubid}/members/{user.userid}", status=404)

        assert user in group.members

    def test_me_alias(self, app, db_session, factories):
        group, other_group = factories.Group.create_batch(size=2)
        user, other_user = factories.User.create_batch(size=2)
        db_session.add_all(
            [
                GroupMembership(group=group, user=user),
                GroupMembership(group=other_group, user=user),
                GroupMembership(group=group, user=other_user),
            ]
        )
        token = factories.DeveloperToken(user=user)
        db_session.commit()

        app.delete(
            f"/api/groups/{group.pubid}/members/me",
            headers=token_authorization_header(token),
        )

        assert user not in group.members
        assert user in other_group.members
        assert other_user in group.members

    def test_me_alias_when_not_authenticated(self, app, factories, db_session):
        group = factories.Group()
        db_session.commit()

        app.delete(f"/api/groups/{group.pubid}/members/me", status=404)

    def test_when_group_not_found(self, app, db_session, factories):
        user = factories.User()
        token = factories.DeveloperToken(user=user)
        db_session.commit()

        app.delete(
            f"/api/groups/DOESNT_EXIST/members/{user.userid}",
            headers=token_authorization_header(token),
            status=404,
        )

    def test_when_user_not_found(self, app, db_session, factories):
        user = factories.User.build()  # `user` has a valid userid but isn't in the DB.
        group = factories.Group()
        authenticated_user = factories.User()
        db_session.add(
            GroupMembership(
                group=group, user=authenticated_user, roles=[GroupMembershipRoles.OWNER]
            )
        )
        token = factories.DeveloperToken(user=authenticated_user)
        db_session.commit()

        app.delete(
            f"/api/groups/{group.pubid}/members/{user.userid}",
            headers=token_authorization_header(token),
            status=404,
        )

    def test_when_userid_invalid(self, app, db_session, factories):
        group = factories.Group()
        authenticated_user = factories.User()
        db_session.add(
            GroupMembership(
                group=group, user=authenticated_user, roles=[GroupMembershipRoles.OWNER]
            )
        )
        token = factories.DeveloperToken(user=authenticated_user)
        db_session.commit()

        app.delete(
            f"/api/groups/{group.pubid}/members/INVALID_USERID",
            headers=token_authorization_header(token),
            status=404,
        )

    def test_when_no_membership(self, app, db_session, factories):
        group = factories.Group()
        target_user = factories.User()  # The target user isn't a member of the group.
        authenticated_user = factories.User()
        db_session.add(
            GroupMembership(
                group=group, user=authenticated_user, roles=[GroupMembershipRoles.OWNER]
            )
        )
        token = factories.DeveloperToken(user=authenticated_user)
        db_session.commit()

        app.delete(
            f"/api/groups/{group.pubid}/members/{target_user.userid}",
            headers=token_authorization_header(token),
            status=404,
        )


class TestEditMembership:
    def test_it(self, do_request, group, target_user, db_session):
        response = do_request()

        assert response.json["userid"] == target_user.userid
        assert response.json["roles"] == ["member"]
        assert response.json["actions"] == [
            "delete",
            "updates.roles.member",
            "updates.roles.moderator",
        ]
        membership = db_session.scalars(
            select(GroupMembership)
            .where(GroupMembership.group == group)
            .where(GroupMembership.user == target_user)
        ).one()
        assert membership.roles == ["member"]

    def test_when_not_authenticated(self, do_request, headers):
        del headers["Authorization"]

        do_request(status=404)

    def test_when_not_authorized(self, do_request):
        do_request(json={"roles": [GroupMembershipRoles.OWNER]}, status=404)

    def test_with_unknown_pubid(self, do_request):
        do_request(pubid="UNKNOWN", status=404)

    def test_with_unknown_userid(self, do_request, group):
        do_request(userid=f"acct:UNKNOWN@{group.authority}", status=404)

    def test_with_invalid_userid(self, do_request):
        do_request(userid=f"INVALID_USERID", status=404)

    def test_when_membership_doesnt_exist(self, do_request, factories):
        do_request(userid=factories.User().userid, status=404)

    def test_me_alias(self, do_request, db_session, group, authenticated_user):
        response = do_request(userid="me")

        assert response.json["userid"] == authenticated_user.userid
        assert response.json["roles"] == ["member"]
        assert response.json["actions"] == ["delete"]
        membership = db_session.scalars(
            select(GroupMembership)
            .where(GroupMembership.group == group)
            .where(GroupMembership.user == authenticated_user)
        ).one()
        assert membership.roles == ["member"]

    def test_me_alias_when_not_authorized(self, do_request):
        do_request(
            userid="me", json={"roles": [GroupMembershipRoles.OWNER]}, status=404
        )

    def test_with_unknown_role(self, do_request):
        response = do_request(json={"roles": ["UNKNOWN"]}, status=400)

        assert response.json["reason"].startswith("roles.0: 'UNKNOWN' is not one of [")

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def target_user(self, db_session, factories, group):
        target_user = factories.User()
        db_session.add(
            GroupMembership(
                group=group, user=target_user, roles=[GroupMembershipRoles.MODERATOR]
            )
        )
        return target_user

    @pytest.fixture
    def authenticated_user(self, db_session, factories, group):
        authenticated_user = factories.User()
        db_session.add(
            GroupMembership(
                group=group, user=authenticated_user, roles=[GroupMembershipRoles.ADMIN]
            )
        )
        return authenticated_user

    @pytest.fixture
    def headers(self, factories, authenticated_user):
        return token_authorization_header(
            factories.DeveloperToken(user=authenticated_user)
        )

    @pytest.fixture
    def do_request(self, app, db_session, group, target_user, headers):
        def do_request(
            pubid=group.pubid,
            userid=target_user.userid,
            json={"roles": ["member"]},
            headers=headers,
            status=200,
        ):
            db_session.commit()
            return app.patch_json(
                f"/api/groups/{pubid}/members/{userid}",
                json,
                headers=headers,
                status=status,
            )

        return do_request


def token_authorization_header(token) -> dict:
    """Return an Authorization header for the given developer token."""
    return {"Authorization": "Bearer {}".format(token.value)}


@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.INFO)
    return caplog

import elasticsearch_dsl
import pytest

from h.models import GroupMembership, GroupMembershipRoles, ModerationStatus

pytestmark = pytest.mark.usefixtures("init_elasticsearch")


class TestSearchAnnotations:
    @pytest.mark.parametrize("nipsa", [True, False])
    @pytest.mark.parametrize("shared", [True, False])
    @pytest.mark.parametrize("moderation_status", ModerationStatus)
    @pytest.mark.parametrize("group_role", [None, *GroupMembershipRoles])
    def test_users_can_see_their_own_annotations(
        self,
        user,
        nipsa,
        shared,
        moderation_status,
        group_role,
        group,
        make_annotation,
        call_search_api,
    ):
        if group_role:
            group.memberships.append(GroupMembership(user=user, roles=[group_role]))
        user.nipsa = nipsa
        annotation = make_annotation(
            user, shared=shared, moderation_status=moderation_status
        )

        response = call_search_api()

        assert annotation.id in response.annotation_ids

    @pytest.mark.parametrize("shared", [True, False])
    @pytest.mark.parametrize("moderation_status", ModerationStatus)
    @pytest.mark.parametrize("group_role", [None, *GroupMembershipRoles])
    def test_users_cant_see_nipsad_users_annotations(
        self,
        moderation_status,
        other_user,
        shared,
        group_role,
        user,
        group,
        make_annotation,
        call_search_api,
    ):
        other_user.nipsa = True
        if group_role:
            group.memberships.append(GroupMembership(user=user, roles=[group_role]))
        annotation = make_annotation(
            other_user, shared=shared, moderation_status=moderation_status
        )

        response = call_search_api()

        assert annotation.id not in response.annotation_ids

    @pytest.mark.parametrize("moderation_status", ModerationStatus)
    @pytest.mark.parametrize("group_role", [None, *GroupMembershipRoles])
    def test_users_cant_see_other_users_private_annotations(
        self,
        moderation_status,
        other_user,
        group_role,
        user,
        group,
        make_annotation,
        call_search_api,
    ):
        if group_role:
            group.memberships.append(GroupMembership(user=user, roles=[group_role]))
        annotation = make_annotation(
            other_user, shared=False, moderation_status=moderation_status
        )

        response = call_search_api()

        assert annotation.id not in response.annotation_ids

    def test_users_cant_see_deleted_annotations(
        self, app, auth_header, user, es_client, make_annotation, call_search_api
    ):
        annotation = make_annotation(
            user, shared=True, moderation_status=ModerationStatus.APPROVED
        )
        app.delete(
            f"/api/annotations/{annotation.id}", headers={"Authorization": auth_header}
        )
        elasticsearch_dsl.Index(es_client.index, using=es_client.conn).refresh()

        response = call_search_api()

        assert annotation.id not in response.annotation_ids

    @pytest.mark.parametrize("nipsa", [True, False])
    @pytest.mark.parametrize("shared", [True, False])
    @pytest.mark.parametrize("moderation_status", ModerationStatus)
    def test_users_cant_see_annotations_in_private_groups(
        self,
        factories,
        make_annotation,
        other_user,
        call_search_api,
        nipsa,
        shared,
        moderation_status,
    ):
        other_user.nipsa = nipsa
        private_group = factories.Group()
        annotation = make_annotation(
            user=other_user,
            group=private_group,
            shared=shared,
            moderation_status=moderation_status,
        )

        response = call_search_api()

        assert annotation.id not in response.annotation_ids

    @pytest.mark.parametrize(
        "nipsa,shared,moderation_status,can_see",
        [
            (False, True, ModerationStatus.PENDING, False),
            (False, True, ModerationStatus.APPROVED, True),
            (False, True, ModerationStatus.DENIED, False),
            (False, True, ModerationStatus.SPAM, False),
            (False, False, ModerationStatus.PENDING, False),
            (False, False, ModerationStatus.APPROVED, False),
            (False, False, ModerationStatus.DENIED, False),
            (False, False, ModerationStatus.SPAM, False),
            (True, True, ModerationStatus.PENDING, False),
            (True, True, ModerationStatus.APPROVED, False),
            (True, True, ModerationStatus.DENIED, False),
            (True, True, ModerationStatus.SPAM, False),
            (True, False, ModerationStatus.PENDING, False),
            (True, False, ModerationStatus.APPROVED, False),
            (True, False, ModerationStatus.DENIED, False),
            (True, False, ModerationStatus.SPAM, False),
        ],
    )
    def test_when_unauthenticated_users_can_see_annotations(
        self,
        nipsa,
        shared,
        moderation_status,
        can_see,
        user,
        make_annotation,
        call_search_api,
    ):
        user.nipsa = nipsa
        annotation = make_annotation(
            user, moderation_status=moderation_status, shared=shared
        )

        response = call_search_api(authenticated=False)

        if can_see:
            assert annotation.id in response.annotation_ids
        else:
            assert annotation.id not in response.annotation_ids

    @pytest.mark.parametrize(
        "params",
        [
            {
                "moderation_status": ModerationStatus.PENDING,
                "group_role": None,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.PENDING,
                "group_role": GroupMembershipRoles.MEMBER,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.PENDING,
                "group_role": GroupMembershipRoles.MODERATOR,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.PENDING,
                "group_role": GroupMembershipRoles.ADMIN,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.PENDING,
                "group_role": GroupMembershipRoles.OWNER,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.APPROVED,
                "group_role": None,
                "can_see": True,
            },
            {
                "moderation_status": ModerationStatus.APPROVED,
                "group_role": GroupMembershipRoles.MEMBER,
                "can_see": True,
            },
            {
                "moderation_status": ModerationStatus.APPROVED,
                "group_role": GroupMembershipRoles.MODERATOR,
                "can_see": True,
            },
            {
                "moderation_status": ModerationStatus.APPROVED,
                "group_role": GroupMembershipRoles.ADMIN,
                "can_see": True,
            },
            {
                "moderation_status": ModerationStatus.APPROVED,
                "group_role": GroupMembershipRoles.OWNER,
                "can_see": True,
            },
            {
                "moderation_status": ModerationStatus.DENIED,
                "group_role": None,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.DENIED,
                "group_role": GroupMembershipRoles.MEMBER,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.DENIED,
                "group_role": GroupMembershipRoles.MODERATOR,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.DENIED,
                "group_role": GroupMembershipRoles.ADMIN,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.DENIED,
                "group_role": GroupMembershipRoles.OWNER,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.SPAM,
                "group_role": None,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.SPAM,
                "group_role": GroupMembershipRoles.MEMBER,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.SPAM,
                "group_role": GroupMembershipRoles.MODERATOR,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.SPAM,
                "group_role": GroupMembershipRoles.ADMIN,
                "can_see": False,
            },
            {
                "moderation_status": ModerationStatus.SPAM,
                "group_role": GroupMembershipRoles.OWNER,
                "can_see": False,
            },
        ],
    )
    def test_when_users_can_see_other_users_annotations(
        self, other_user, params, user, group, make_annotation, call_search_api
    ):
        if params["group_role"]:
            group.memberships.append(
                GroupMembership(user=user, roles=[params["group_role"]])
            )
        other_users_annotation = make_annotation(
            other_user,
            moderation_status=params["moderation_status"],
            shared=True,
        )

        response = call_search_api()

        if params["can_see"]:
            assert other_users_annotation.id in response.annotation_ids
        else:
            assert other_users_annotation.id not in response.annotation_ids

    def test_user_filter(self, make_annotation, other_user, call_search_api, user):
        own_annotation = make_annotation(user)
        other_users_annotation = make_annotation(other_user, shared=True)

        response = call_search_api(params={"user": other_user.userid})

        assert own_annotation.id not in response.annotation_ids
        assert other_users_annotation.id in response.annotation_ids

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def other_user(self, factories):
        return factories.User()

    @pytest.fixture
    def group(self, factories):
        return factories.OpenGroup()

    @pytest.fixture
    def auth_header(self, factories, user):
        return f"Bearer {factories.DeveloperToken(user=user).value}"

    @pytest.fixture
    def make_annotation(self, app, db_session, factories, group):
        def make_annotation(user, group=group, **kwargs):
            annotation = factories.Annotation(
                userid=user.userid, groupid=group.pubid, **kwargs
            )
            db_session.commit()

            # Index `annotation` into Elasticsearch.
            #
            # Normally when a new annotation is created by calling the API the
            # annotation is both committed to the DB and indexed into
            # Elasticsearch.  But if tests have been creating annotations by
            # writing to the DB directly (e.g. by using test factories) rather
            # than by calling the API, those annotations will be in the DB but
            # not in Elasticsearch.
            #
            # Index `annotation` into Elasticsearch so that it'll show up in
            # subsequent search API responses.
            app.post(f"/api/annotations/{annotation.id}/reindex", {})

            return annotation

        return make_annotation

    @pytest.fixture
    def call_search_api(self, app, auth_header):
        def call_search_api(*, authenticated=True, params=None):
            headers = {}

            if authenticated:
                headers["Authorization"] = auth_header

            response = app.get("/api/search", headers=headers, params=params)
            response.annotation_ids = {anno["id"] for anno in response.json["rows"]}
            return response

        return call_search_api


class TestGetAnnotation:
    def test_it_returns_annotation_if_shared(self, app, annotation):
        # Unauthenticated users may view shared annotations assuming they have
        # group access.

        res = app.get(
            "/api/annotations/" + annotation.id, headers={"accept": "application/json"}
        )
        data = res.json
        assert data["id"] == annotation.id
        assert data["permissions"]["read"] == ["group:__world__"]

    def test_it_returns_http_404_for_private_annotation_when_unauthenticated(
        self, app, private_annotation
    ):
        res = app.get(
            "/api/annotations/" + private_annotation.id,
            headers={"accept": "application/json"},
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_for_private_annotation_when_unauthorized(
        self, app, private_annotation, user_with_token
    ):
        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        res = app.get(
            "/api/annotations/" + private_annotation.id,
            headers=headers,
            expect_errors=True,
        )

        assert res.status_code == 404


class TestGetAnnotationJSONLD:
    def test_it_returns_annotation_if_shared(self, app, annotation):
        # Unauthenticated users may view shared annotations assuming they have
        # group access.

        res = app.get(
            "/api/annotations/" + annotation.id + ".jsonld",
            headers={"accept": "application/json"},
        )
        data = res.json

        # In JSON-LD, the ID will be a URI per spec
        # That URI does, however, contain the annotation's ID
        assert data["@context"] == "http://www.w3.org/ns/anno.jsonld"
        assert data["id"] == "http://example.com/a/" + annotation.id

    def test_it_returns_http_404_for_private_annotation_when_unauthenticated(
        self, app, private_annotation
    ):
        res = app.get(
            "/api/annotations/" + private_annotation.id + ".jsonld",
            headers={"accept": "application/json"},
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_for_private_annotation_when_unauthorized(
        self, app, private_annotation, user_with_token
    ):
        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        res = app.get(
            "/api/annotations/" + private_annotation.id + ".jsonld",
            headers=headers,
            expect_errors=True,
        )

        assert res.status_code == 404


class TestPostAnnotation:
    def test_it_returns_http_404_if_unauthorized(self, app):
        # FIXME: This should return a 403  # noqa: FIX001, TD001, TD002, TD003

        # This isn't a valid payload, but it won't get validated because the
        # authorization will fail first
        annotation = {"text": "My annotation", "uri": "http://example.com"}

        res = app.post_json("/api/annotations", annotation, expect_errors=True)

        assert res.status_code == 404

    @pytest.mark.xfail
    def test_it_returns_http_403_if_unauthorized(self, app):
        annotation = {"text": "My annotation", "uri": "http://example.com"}

        res = app.post_json("/api/annotations", annotation, expect_errors=True)

        assert res.status_code == 403

    def test_it_returns_http_400_if_group_forbids_write(
        self, app, user_with_token, non_writeable_group
    ):
        # Write an annotation to a group that doesn't allow writes.

        # This is a basic test to check that h is correctly configuring
        # principals_for_userid.

        user, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        annotation = {
            "group": non_writeable_group.pubid,
            "permissions": {
                "read": [f"group:{non_writeable_group.pubid}"],
                "admin": [user.userid],
                "update": [user.userid],
                "delete": [user.userid],
            },
            "text": "My annotation",
            "uri": "http://example.com",
        }

        res = app.post_json(
            "/api/annotations", annotation, headers=headers, expect_errors=True
        )

        assert res.status_code == 400
        assert res.json["reason"].startswith("group:")

    # TODO: This endpoint should return a 201  # noqa: FIX002, TD002, TD003
    def test_it_returns_http_200_when_annotation_created(self, app, user_with_token):
        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        annotation = {
            "group": "__world__",
            "text": "My annotation",
            "uri": "http://example.com",
        }

        res = app.post_json("/api/annotations", annotation, headers=headers)

        assert res.status_code == 200


class TestPatchAnnotation:
    def test_it_updates_annotation_if_authorized(
        self, app, user_annotation, user_with_token
    ):
        # An annotation's creator (user) is blessed with the 'update'
        # permission.

        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        annotation_patch = {"text": "This is an updated annotation"}

        res = app.patch_json(
            f"/api/annotations/{user_annotation.id}",
            annotation_patch,
            headers=headers,
        )

        assert res.json["text"] == "This is an updated annotation"
        assert res.status_code == 200

    @pytest.mark.parametrize(
        "pre_moderation_enabled,moderation_status,expected_moderation_status",
        [
            # Editing a private annotation and making it shared might change its annotation state, depending on the current state:
            # If the group has pre-moderation disabled the annotation's moderation state becomes Approved.
            (False, None, ModerationStatus.APPROVED),
            # If the group has pre-moderation enabled the annotation's moderation state becomes Pending.
            (True, None, ModerationStatus.PENDING),
            # If a private annotation whose state is Denied is edited and made shared the state becomes Pending.
            (True, ModerationStatus.DENIED, ModerationStatus.PENDING),
            # If a private annotation whose state is Pending or Spam is edited and made shared the state doesn't change.
            (True, ModerationStatus.PENDING, ModerationStatus.PENDING),
            (True, ModerationStatus.SPAM, ModerationStatus.SPAM),
        ],
    )
    def test_sharing_a_private_annotation(
        self,
        app,
        user_with_token,
        user_private_annotation,
        db_session,
        pre_moderation_enabled,
        moderation_status,
        expected_moderation_status,
    ):
        user, token = user_with_token
        group = user_private_annotation.group
        group.pre_moderated = pre_moderation_enabled
        user_private_annotation.moderation_status = moderation_status
        db_session.commit()

        headers = {"Authorization": f"Bearer {token.value}"}
        annotation_patch = {
            "permissions": {
                "read": [f"group:{group.pubid}"],
                "admin": [user.userid],
                "updated": [user.userid],
                "deleted": [user.userid],
            },
            "text": "PRIVATE",
        }

        res = app.patch_json(
            f"/api/annotations/{user_private_annotation.id}",
            annotation_patch,
            headers=headers,
        )

        assert res.status_code == 200
        db_session.refresh(user_private_annotation)
        assert user_private_annotation.shared
        assert user_private_annotation.moderation_status == expected_moderation_status

    @pytest.mark.parametrize(
        "pre_moderation_enabled,moderation_status,expected_moderation_status",
        # Private annotations don't always have the NULL state: if a shared annotation is edited and made private it retains its previous state from when it was shared
        # (Pending, Approved, Denied, or Spam).
        [
            (True, ModerationStatus.PENDING, ModerationStatus.PENDING),
            (True, ModerationStatus.APPROVED, ModerationStatus.APPROVED),
            (True, ModerationStatus.SPAM, ModerationStatus.SPAM),
            (True, ModerationStatus.DENIED, ModerationStatus.DENIED),
            (False, ModerationStatus.APPROVED, ModerationStatus.APPROVED),
            (False, ModerationStatus.SPAM, ModerationStatus.SPAM),
            (False, ModerationStatus.DENIED, ModerationStatus.DENIED),
            (False, ModerationStatus.PENDING, ModerationStatus.PENDING),
        ],
    )
    def test_making_annotation_private(
        self,
        app,
        user_with_token,
        user_shared_annotation,
        db_session,
        pre_moderation_enabled,
        moderation_status,
        expected_moderation_status,
    ):
        user, token = user_with_token
        group = user_shared_annotation.group
        group.pre_moderated = pre_moderation_enabled
        user_shared_annotation.moderation_status = moderation_status
        db_session.commit()

        headers = {"Authorization": f"Bearer {token.value}"}
        annotation_patch = {
            "permissions": {
                "read": [user.userid],
                "admin": [user.userid],
                "updated": [user.userid],
                "deleted": [user.userid],
            },
            "text": "PRIVATE",
        }

        res = app.patch_json(
            f"/api/annotations/{user_shared_annotation.id}",
            annotation_patch,
            headers=headers,
        )

        assert res.status_code == 200
        db_session.refresh(user_shared_annotation)
        assert not user_shared_annotation.shared
        assert user_shared_annotation.moderation_status == expected_moderation_status

    def test_it_returns_http_404_if_unauthenticated(self, app, user_annotation):
        annotation_patch = {"text": "whatever"}

        res = app.patch_json(
            f"/api/annotations/{user_annotation.id}",
            annotation_patch,
            expect_errors=True,
        )

        assert res.status_code == 404

    def test_it_returns_http_404_if_unauthorized(
        self, app, annotation, user_with_token
    ):
        # The user in this request is not the annotation's creator.

        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}

        annotation_patch = {"text": "whatever"}

        res = app.patch_json(
            f"/api/annotations/{annotation.id}",
            annotation_patch,
            headers=headers,
            expect_errors=True,
        )

        assert res.status_code == 404


class TestDeleteAnnotation:
    def test_it_deletes_annotation_if_authorized(
        self, app, user_annotation, user_with_token
    ):
        # An annotation's creator (user) is blessed with the 'update'
        # permission.

        _, token = user_with_token

        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.delete(f"/api/annotations/{user_annotation.id}", headers=headers)

        assert res.status_code == 200
        assert res.json["id"] == user_annotation.id

    def test_it_returns_http_404_if_unauthenticated(self, app, user_annotation):
        res = app.delete(f"/api/annotations/{user_annotation.id}", expect_errors=True)

        assert res.status_code == 404

    def test_it_returns_http_404_if_unauthorized(
        self, app, annotation, user_with_token
    ):
        # The user in this request is not the annotation's creator.

        _, token = user_with_token
        headers = {"Authorization": f"Bearer {token.value}"}

        res = app.delete(
            f"/api/annotations/{annotation.id}",
            headers=headers,
            expect_errors=True,
        )

        assert res.status_code == 404


@pytest.fixture
def annotation(db_session, factories):
    ann = factories.Annotation(
        userid="acct:testuser@example.com", groupid="__world__", shared=True
    )
    db_session.commit()
    return ann


@pytest.fixture
def private_annotation(db_session, factories):
    ann = factories.Annotation(
        userid="acct:testuser@example.com", groupid="__world__", shared=False
    )
    db_session.commit()
    return ann


@pytest.fixture
def user(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def user_annotation(db_session, user, factories):
    ann = factories.Annotation(userid=user.userid, groupid="__world__", shared=True)
    db_session.commit()
    return ann


@pytest.fixture
def user_shared_annotation(db_session, user, factories):
    group = factories.OpenGroup()
    ann = factories.Annotation(userid=user.userid, groupid=group.pubid, shared=True)
    db_session.commit()
    return ann


@pytest.fixture
def user_private_annotation(db_session, user, factories):
    group = factories.OpenGroup()
    ann = factories.Annotation(userid=user.userid, groupid=group.pubid, shared=False)
    db_session.commit()
    return ann


@pytest.fixture
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(user=user)
    db_session.add(token)
    db_session.commit()
    return (user, token)


@pytest.fixture
def auth_client(db_session, factories):
    auth_client = factories.AuthClient(authority="thirdparty.example.org")
    db_session.commit()
    return auth_client


@pytest.fixture
def non_writeable_group(db_session, factories):
    group = factories.Group(writeable_by=None)
    db_session.commit()
    return group

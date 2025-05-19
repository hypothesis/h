import pytest

from h.models.annotation import ModerationStatus

pytestmark = pytest.mark.usefixtures("init_elasticsearch")


class TestSearchAnnotations:
    @pytest.mark.parametrize("author_is_nipsaed", [True, False])
    @pytest.mark.parametrize("api_user_is_author", [True, False])
    def test_hidden_and_nipsa(
        self,
        app,
        make_annotation,
        author_is_nipsaed,
        api_user_is_author,
        make_user,
    ):
        author = make_user(nipsa=author_is_nipsaed)
        other_user = make_user()
        anno_from_author = make_annotation(user=author)
        private_anno_from_author = make_annotation(user=author, shared=False)
        hidden_anno_from_author = make_annotation(
            user=author, moderation_status=ModerationStatus.DENIED
        )
        annotation_from_other_user = make_annotation(user=other_user)

        search_annotation_ids = self.search(
            app, author if api_user_is_author else other_user
        )

        expected_ids = set()
        not_expected_ids = set()
        if api_user_is_author:
            expected_ids = {
                # We'd expect to see all our own annotations
                anno_from_author.id,
                private_anno_from_author.id,
                hidden_anno_from_author.id,
                # And the other user annotation
                annotation_from_other_user.id,
            }
        else:
            # We should always see our own annos
            expected_ids = {annotation_from_other_user.id}
            # And never see hidden or private annos from other users
            not_expected_ids = {private_anno_from_author.id, hidden_anno_from_author.id}
            if author_is_nipsaed:
                # If another user is nipsaed we should not see any of their annotations
                not_expected_ids.add(anno_from_author.id)
            else:
                # If the author is not nipsaed we should see their annotations if they are shared/not hidden
                expected_ids.add(anno_from_author.id)

        assert expected_ids.issubset(search_annotation_ids)
        assert search_annotation_ids.isdisjoint(not_expected_ids)

    @pytest.mark.parametrize("author_is_nipsaed", [True, False])
    @pytest.mark.parametrize("api_user_is_author", [True, False])
    def test_user_filter(
        self,
        app,
        make_annotation,
        author_is_nipsaed,
        api_user_is_author,
        make_user,
    ):
        author = make_user(nipsa=author_is_nipsaed)
        other_user = make_user()
        anno_from_author = make_annotation(user=author)
        private_anno_from_author = make_annotation(user=author, shared=False)
        hidden_anno_from_author = make_annotation(
            user=author, moderation_status=ModerationStatus.DENIED
        )
        annotation_from_user = make_annotation(user=other_user)

        # Filter by author.userid
        search_annotation_ids = self.search(
            app, author if api_user_is_author else other_user, user=author.userid
        )

        expected_ids = set()
        not_expected_ids = set()
        if api_user_is_author:
            expected_ids = {
                anno_from_author.id,
                private_anno_from_author.id,
                hidden_anno_from_author.id,
            }
            not_expected_ids = {annotation_from_user.id}
        else:
            # We are filtering by another user, we should see any of our own annotations
            # But also any of the hidden annos of that user
            not_expected_ids = {
                private_anno_from_author.id,
                hidden_anno_from_author.id,
                annotation_from_user.id,
            }
            if author_is_nipsaed:
                # If another user is nipsaed we should not see any of their annotations
                not_expected_ids.add(anno_from_author.id)
            else:
                # If the author is not nipsaed we should see their annotations if they are shared/not hidden
                expected_ids.add(anno_from_author.id)

        assert expected_ids.issubset(search_annotation_ids)
        assert search_annotation_ids.isdisjoint(not_expected_ids)

    def search(self, app, api_user, **kwargs) -> set[str]:
        token = api_user.tokens[0]
        headers = {"Authorization": f"Bearer {token.value}"}
        res = app.get("/api/search", headers=headers, params=kwargs)
        return {a["id"] for a in res.json["rows"]}

    @pytest.fixture
    def make_annotation(self, app, factories, db_session):
        def _make_annotation(user, groupid="__world__", shared=True, **kwargs):  # noqa: FBT002
            api_token = user.tokens[0]
            annotation = factories.Annotation(
                shared=shared, userid=user.userid, groupid=groupid, **kwargs
            )
            db_session.commit()
            headers = {"Authorization": f"Bearer {api_token.value}"}
            res = app.post(
                f"/api/annotations/{annotation.id}/reindex",
                {},
                headers=headers,
            )

            assert res.status_code == 200
            return annotation

        return _make_annotation

    @pytest.fixture
    def make_user(self, factories):
        def _make_user(**kwargs):
            user = factories.User(**kwargs)
            factories.DeveloperToken(user=user)
            return user

        return _make_user


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

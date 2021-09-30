import pytest


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
        # FIXME: This should return a 403

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

    # TODO: This endpoint should return a 201
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
def user_with_token(user, db_session, factories):
    token = factories.DeveloperToken(userid=user.userid)
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

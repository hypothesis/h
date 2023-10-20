import json

import pytest


@pytest.mark.usefixtures("with_clean_db")
class TestBulkAnnotation:
    def test_it_requires_authentication(self, make_request):
        response = make_request(headers={"bad_auth": "BAD"}, expect_errors=True)

        assert response.status_int == 404

    def test_it_rejects_an_invalid_request(self, make_request):
        response = make_request({}, expect_errors=True)

        assert response.status_int == 400

    def test_it_accepts_a_valid_request(self, make_request, factories):
        # We'll make the viewer the author for simplicity
        user = factories.User(
            authority="lms.hypothes.is", username="111111111122222222223333333333"
        )
        group = factories.Group(
            authority="lms.hypothes.is",
            authority_provided_id="1234567890",
            members=[user],
        )
        annotation_slim = factories.AnnotationSlim(
            user=user,
            group=group,
            shared=True,
            deleted=False,
            created="2018-11-13T20:20:39",
        )
        factories.AnnotationMetadata(
            annotation_slim=annotation_slim, data={"some": "value"}
        )

        response = make_request(
            {
                "filter": {
                    "limit": 20,
                    "audience": {"username": [user.username]},
                    "created": {
                        "gt": "2018-11-12T20:20:39+00:00",
                        "lte": "2018-11-13T20:20:39+00:00",
                    },
                },
                "fields": ["author.username", "group.authority_provided_id"],
            }
        )

        assert response.status_int == 200
        assert response.content_type == "application/x-ndjson"
        assert (
            response.headers["Hypothesis-Media-Type"]
            == "application/vnd.hypothesis.v1+x-ndjson"
        )

        lines = response.body.decode("utf-8").split("\n")
        data = [json.loads(line) for line in lines if line]
        assert data == [
            {
                "group": {"authority_provided_id": group.authority_provided_id},
                "author": {"username": user.username},
                "metadata": {"some": "value"},
            }
        ]

    @pytest.fixture
    def make_request(self, app, auth_header_for_authority):
        def make_request(json_body=None, expect_errors=False, headers=None):
            return app.post(
                "/api/bulk/annotation",
                json.dumps(json_body or {}),
                headers=headers or auth_header_for_authority("lms.hypothes.is"),
                content_type="application/json",
                expect_errors=expect_errors,
            )

        return make_request

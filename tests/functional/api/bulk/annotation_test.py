import json

import pytest
from h_matchers import Any


@pytest.mark.usefixtures("with_clean_db")
class TestBulkAnnotation:
    def test_it_requires_authentication(self, make_request):
        response = make_request(headers={"bad_auth": "BAD"}, expect_errors=True)

        assert response.status_int == 404

    def test_it_rejects_an_invalid_request(self, make_request):
        response = make_request({}, expect_errors=True)

        assert response.status_int == 400

    def test_it_accepts_a_valid_request(self, make_request):
        response = make_request(
            {
                "filter": {
                    "limit": 20,
                    "audience": {"username": ["3a022b6c146dfd9df4ea8662178eac"]},
                    "updated": {
                        "gt": "2018-11-13T20:20:39+00:00",
                        "lte": "2018-11-13T20:20:39+00:00",
                    },
                },
                "fields": ["group.authority_provided_id", "author.username"],
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
        assert data == Any.list.comprised_of(
            {
                "group": {"authority_provided_id": Any.string()},
                "author": {"username": Any.string()},
            }
        )

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

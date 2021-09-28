"""
Test the versioning of our API using Accept headers
"""


class TestIndexEndpointVersions:
    def test_index_sets_version_response_header(self, app):
        """
        A custom response header should be present confirming the version of
        the API used.
        """
        res = app.get("/api/")

        assert res.status_code == 200
        assert "Hypothesis-Media-Type" in res.headers
        assert (
            res.headers["Hypothesis-Media-Type"] == "application/vnd.hypothesis.v1+json"
        )

    def test_index_200s_when_accept_empty(self, app):
        """
        Don't send any Accept headers and we should get a 200 response.
        """
        res = app.get("/api/")

        assert res.status_code == 200
        assert "links" in res.json

    def test_index_200s_with_application_json(self, app):
        """
        Send ``application/json`` and we should get a 200 response from the
        default version.
        """
        headers = {"Accept": str("application/json")}

        res = app.get("/api/", headers=headers)

        assert res.status_code == 200
        assert "links" in res.json

    def test_index_200s_with_v1_header(self, app):
        """
        Set a v1 Accept header and we should get a 200 response.
        """
        headers = {"Accept": str("application/vnd.hypothesis.v1+json")}

        res = app.get("/api/", headers=headers)

        assert res.status_code == 200
        assert "links" in res.json

    def test_index_200s_with_v2_header(self, app):
        """
        Set a v2 Accept header and we should get a 200 response.
        """
        headers = {"Accept": str("application/vnd.hypothesis.v2+json")}

        res = app.get("/api/", headers=headers)

        assert res.status_code == 200
        assert "links" in res.json

    def test_index_406s_with_invalid_version_header(self, app):
        """
        Set a v3 Accept header and we should get a 406 response.
        (For now because the version doesn't exist yet)
        """
        headers = {"Accept": str("application/vnd.hypothesis.v3+json")}

        res = app.get("/api/", headers=headers, expect_errors=True)

        assert res.status_code == 406

    def test_index_200s_with_invalid_accept_header_value(self, app):
        """
        Set a generally-invalid Accept header and we should get a 200.
        """
        headers = {"Accept": str("nonsensical")}

        res = app.get("/api/", headers=headers, expect_errors=True)

        assert res.status_code == 200
        assert "links" in res.json
        assert (
            res.headers["Hypothesis-Media-Type"] == "application/vnd.hypothesis.v1+json"
        )

    def test_index_adds_v1_response_header(self, app):
        """
        An Accept header with the value of 'application/json' will be serviced
        by the default version of the API, which is v1
        """

        res = app.get("/api/")

        assert (
            res.headers["Hypothesis-Media-Type"] == "application/vnd.hypothesis.v1+json"
        )

    def test_index_adds_v2_response_header(self, app):
        """
        Set a v2 Accept header and we should get a version media type
        response header.
        """
        headers = {"Accept": str("application/vnd.hypothesis.v2+json")}

        res = app.get("/api/", headers=headers)

        assert (
            res.headers["Hypothesis-Media-Type"] == "application/vnd.hypothesis.v2+json"
        )

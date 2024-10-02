import pytest


class TestGetIndex:
    def test_it_returns_links(self, app):
        res = app.get("/api/")

        assert "links" in res.json
        assert res.status_code == 200

    @pytest.mark.parametrize(
        "media_type",
        ["application/vnd.hypothesis.v1+json", "application/vnd.hypothesis.v2+json"],
    )
    def test_it_supports_versions(self, app, media_type):
        headers = {"accept": media_type}

        res = app.get("/api/", headers=headers)

        assert res.headers["Hypothesis-Media-Type"] == media_type

    def test_it_returns_links_for_resources(self, app):
        res = app.get("/api/")

        for resource in ["annotation", "group", "user", "profile", "search", "links"]:
            assert resource in res.json["links"]

    @pytest.mark.parametrize(
        "resource,expected_services",
        [
            (
                "annotation",
                ["create", "read", "update", "delete", "flag", "hide", "unhide"],
            ),
            ("group", ["create", "read", "update"]),
            ("profile", ["read", "update"]),
            ("user", ["create", "update"]),
        ],
    )
    def test_it_returns_expected_resource_service_links_for_v1(
        self, app, resource, expected_services
    ):
        res = app.get("/api/")

        for service in expected_services:
            assert service in res.json["links"][resource]
            assert "method" in res.json["links"][resource][service]
            assert "url" in res.json["links"][resource][service]

    @pytest.mark.parametrize(
        "resource,nested_resource,expected_services",
        [("profile", "groups", ["read"]), ("group", "member", ["add", "delete"])],
    )
    def test_it_returns_expected_nested_resource_service_links_for_v1(
        self, app, resource, nested_resource, expected_services
    ):
        res = app.get("/api/")

        assert nested_resource in res.json["links"][resource]

        for service in expected_services:
            assert service in res.json["links"][resource][nested_resource]
            assert "method" in res.json["links"][resource][nested_resource][service]
            assert "url" in res.json["links"][resource][nested_resource][service]

    @pytest.mark.parametrize(
        "resource,expected_services",
        [
            (
                "annotation",
                ["create", "read", "update", "delete", "flag", "hide", "unhide"],
            ),
            ("group", ["create", "read", "update"]),
            ("profile", ["read", "update"]),
            ("user", ["create", "update"]),
        ],
    )
    def test_it_returns_expected_resource_service_links_for_v2(
        self, app, resource, expected_services
    ):
        headers = {"accept": "application/vnd.hypothesis.v2+json"}
        res = app.get("/api/", headers=headers)

        for service in expected_services:
            assert service in res.json["links"][resource]
            assert "method" in res.json["links"][resource][service]
            assert "url" in res.json["links"][resource][service]

    @pytest.mark.parametrize(
        "resource,nested_resource,expected_services",
        [("profile", "groups", ["read"]), ("group", "member", ["add", "delete"])],
    )
    def test_it_returns_expected_nested_resource_service_links_for_v2(
        self, app, resource, nested_resource, expected_services
    ):
        headers = {"accept": "application/vnd.hypothesis.v2+json"}
        res = app.get("/api/", headers=headers)

        assert nested_resource in res.json["links"][resource]

        for service in expected_services:
            assert service in res.json["links"][resource][nested_resource]
            assert "method" in res.json["links"][resource][nested_resource][service]
            assert "url" in res.json["links"][resource][nested_resource][service]

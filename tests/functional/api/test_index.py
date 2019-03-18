# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

# String type for request/response headers and metadata in WSGI.
#
# Per PEP-3333, this is intentionally `str` under both Python 2 and 3, even
# though it has different meanings.
#
# See https://www.python.org/dev/peps/pep-3333/#a-note-on-string-types
native_str = str


@pytest.mark.functional
class TestGetIndex(object):
    def test_it_returns_links(self, app):
        res = app.get("/api/")

        assert "links" in res.json
        assert res.status_code == 200

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
            ("group", ["create", "read", "update", "create_or_update"]),
            ("profile", ["read", "update"]),
            ("user", ["create", "update"]),
        ],
    )
    def test_it_returns_expected_resource_service_links(
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
    def test_it_returns_expected_nested_resource_service_links(
        self, app, resource, nested_resource, expected_services
    ):
        res = app.get("/api/")

        assert nested_resource in res.json["links"][resource]

        for service in expected_services:
            assert service in res.json["links"][resource][nested_resource]
            assert "method" in res.json["links"][resource][nested_resource][service]
            assert "url" in res.json["links"][resource][nested_resource][service]

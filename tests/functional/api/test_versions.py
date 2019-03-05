# -*- coding: utf-8 -*-
"""
Test the versioning of our API using Accept headers
"""

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
class TestIndexEndpointVersions(object):
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

    def test_index_415s_with_invalid_version_header(self, app):
        """
        Set a v2 Accept header and we should get a 415 response.
        (For now because the version doesn't exist quite yet)
        """
        headers = {"Accept": str("application/vnd.hypothesis.v2+json")}

        res = app.get("/api/", headers=headers, expect_errors=True)

        assert res.status_code == 415

    def test_index_415s_with_invalid_accept_header_value(self, app):
        """
        Set a generally-invalid Accept header and we should always get a 415.
        """
        headers = {"Accept": str("nonsensical")}

        res = app.get("/api/", headers=headers, expect_errors=True)

        assert res.status_code == 415

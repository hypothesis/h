import json
from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from h.views.admin.documents import DocumentsAdminViews


class TestDocumentsAdminViews:
    def test_get(self, views):
        assert not views.get()

    def test_update_annotation_urls_schedules_update(
        self, views, pyramid_request, move_annotations_by_url, flash
    ):
        mappings = {"https://example.com": {"url": "https://example.org"}}
        pyramid_request.POST["url_mappings"] = json.dumps(mappings)

        views.update_annotation_urls()

        move_annotations_by_url.chunks.assert_called_once_with(mappings.items(), 10)
        move_annotations_by_url.chunks.return_value.apply_async.assert_called_once()
        flash.assert_called_once_with("URL migration started for 1 URL(s)", "success")

    def test_it_errors_if_json_does_not_parse(
        self, views, pyramid_request, move_annotations_by_url, flash
    ):
        pyramid_request.POST["url_mappings"] = "not-json"

        views.update_annotation_urls()

        flash.assert_called_once_with(
            Any.string.matching("Failed to parse URL mappings:.*"), "error"
        )
        assert pyramid_request.response.status_code == 400
        move_annotations_by_url.chunks.assert_not_called()

    def test_it_errors_if_validation_fails(
        self, views, pyramid_request, move_annotations_by_url, flash
    ):
        pyramid_request.POST["url_mappings"] = json.dumps({"not-a-url": "foo"})

        views.update_annotation_urls()

        flash.assert_called_once_with(
            Any.string.matching("Failed to validate URL mappings:.*"), "error"
        )
        assert pyramid_request.response.status_code == 400
        move_annotations_by_url.chunks.assert_not_called()

    @pytest.fixture(autouse=True)
    def move_annotations_by_url(self, patch):
        return patch("h.views.admin.documents.move_annotations_by_url")

    @pytest.fixture
    def views(self, pyramid_request):
        return DocumentsAdminViews(pyramid_request)

    @pytest.fixture
    def flash(self, pyramid_request):
        flash = create_autospec(pyramid_request.session.flash)
        pyramid_request.session.flash = flash
        return flash

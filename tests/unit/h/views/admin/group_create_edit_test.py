from unittest.mock import sentinel

import pytest

from h.views.admin.group_create_edit import AdminGroupCreateViews, AdminGroupEditViews


class TestAdminGroupCreateViews:
    def test_get(self, views):
        assert views.get() == {}

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminGroupCreateViews(sentinel.context, pyramid_request)


class TestAdminGroupEditViews:
    def test_get(self, views):
        assert views.get() == {}

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminGroupEditViews(sentinel.context, pyramid_request)

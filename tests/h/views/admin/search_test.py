import datetime
from unittest import mock

import pytest

from h.services.group import GroupService
from h.views.admin.search import NotFoundError, SearchAdminViews

pytestmark = pytest.mark.usefixtures("search_index")


class TestSearchAdminViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_reindex_date(self, views, search_index, pyramid_request):
        pyramid_request.params = {
            "start": "2020-09-09",
            "end": "2020-09-11",
        }

        views.reindex_date()

        search_index.add_annotations_between_times.assert_called_once_with(
            datetime.datetime(year=2020, month=9, day=9),
            datetime.datetime(year=2020, month=9, day=11),
            "reindex_date",
        )
        assert pyramid_request.session.peek_flash("success") == [
            "Began reindexing from 2020-09-09 00:00:00 to 2020-09-11 00:00:00"
        ]

    @pytest.mark.parametrize("force", [True, False])
    def test_reindex_user_reindexes_annotations(
        self, views, pyramid_request, search_index, factories, force
    ):
        user = factories.User(username="johnsmith")
        pyramid_request.params = {"username": "johnsmith"}
        if force:
            pyramid_request.params["reindex_user_force"] = "on"

        views.reindex_user()

        search_index.add_users_annotations.assert_called_once_with(
            user.userid, "reindex_user", force=force
        )

        assert pyramid_request.session.peek_flash("success") == [
            f"Began reindexing annotations by {user.userid}"
        ]

    def test_reindex_user_errors_if_user_not_found(self, views, pyramid_request):
        pyramid_request.params = {"username": "johnsmith"}

        with pytest.raises(NotFoundError, match="User johnsmith not found"):
            views.reindex_user()

    @pytest.mark.parametrize("force", [True, False])
    def test_reindex_group_reindexes_annotations(
        self, views, pyramid_request, search_index, factories, group_service, force
    ):
        group = factories.Group(pubid="abc123")
        pyramid_request.params = {"groupid": "abc123"}
        if force:
            pyramid_request.params["reindex_group_force"] = "on"
        group_service.fetch_by_pubid.return_value = group

        views.reindex_group()

        group_service.fetch_by_pubid.assert_called_with(group.pubid)
        search_index.add_group_annotations.assert_called_once_with(
            group.pubid, "reindex_group", force=force
        )

        assert pyramid_request.session.peek_flash("success") == [
            f"Began reindexing annotations in group {group.pubid} ({group.name})"
        ]

    def test_reindex_group_errors_if_group_not_found(
        self, views, pyramid_request, group_service
    ):
        pyramid_request.params = {"groupid": "def456"}
        group_service.fetch_by_pubid.return_value = None

        with pytest.raises(NotFoundError, match="Group def456 not found"):
            views.reindex_group()

    @pytest.fixture
    def views(self, pyramid_request):
        return SearchAdminViews(pyramid_request)

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("admin.search", "/admin/search")


@pytest.fixture
def group_service(pyramid_config):
    service = mock.create_autospec(GroupService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="group")
    return service

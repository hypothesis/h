import datetime
from unittest import mock

import pytest

from h.services.group import GroupService
from h.views.admin.search import NotFoundError, SearchAdminViews


class TestSearchAdminViews:
    def test_get(self, views):
        assert views.get() == {}

    def test_reindex_date(self, views, tasks, pyramid_request):
        pyramid_request.params = {
            "start": "2020-09-09",
            "end": "2020-09-11",
            "name": "sync_annotation",
        }

        views.reindex_date()

        tasks.job_queue.add_annotations_between_times.delay.assert_called_once_with(
            "sync_annotation",
            datetime.datetime(year=2020, month=9, day=9),  # noqa: DTZ001
            datetime.datetime(year=2020, month=9, day=11),  # noqa: DTZ001
            tag="reindex_date",
        )
        assert pyramid_request.session.peek_flash("success") == [
            "Began reindexing from 2020-09-09 00:00:00 to 2020-09-11 00:00:00"
        ]

    @pytest.mark.parametrize("force", [True, False])
    def test_reindex_user_reindexes_annotations(
        self, views, pyramid_request, tasks, factories, force
    ):
        user = factories.User(username="johnsmith")
        pyramid_request.params = {
            "username": "johnsmith",
            "name": "sync_annotation",
        }
        if force:
            pyramid_request.params["reindex_user_force"] = "on"

        views.reindex_user()

        tasks.job_queue.add_annotations_from_user.delay.assert_called_once_with(
            "sync_annotation",
            user.userid,
            tag="reindex_user",
            force=force,
        )

        assert pyramid_request.session.peek_flash("success") == [
            f"Began reindexing annotations by {user.userid}"
        ]

    def test_reindex_user_errors_if_user_not_found(self, views, pyramid_request):
        pyramid_request.params = {"username": "johnsmith", "name": "sync_annotation"}

        with pytest.raises(NotFoundError, match="User johnsmith not found"):
            views.reindex_user()

    @pytest.mark.parametrize("force", [True, False])
    def test_reindex_group_reindexes_annotations(
        self, views, pyramid_request, tasks, factories, group_service, force
    ):
        group = factories.Group(pubid="abc123")
        pyramid_request.params = {"groupid": "abc123", "name": "sync_annotation"}
        if force:
            pyramid_request.params["reindex_group_force"] = "on"
        group_service.fetch_by_pubid.return_value = group

        views.reindex_group()

        group_service.fetch_by_pubid.assert_called_with(group.pubid)
        tasks.job_queue.add_annotations_from_group.delay.assert_called_once_with(
            "sync_annotation",
            group.pubid,
            tag="reindex_group",
            force=force,
        )

        assert pyramid_request.session.peek_flash("success") == [
            f"Began reindexing annotations in group {group.pubid} ({group.name})"
        ]

    def test_reindex_group_errors_if_group_not_found(
        self, views, pyramid_request, group_service
    ):
        pyramid_request.params = {"groupid": "def456", "name": "sync_annotation"}
        group_service.fetch_by_pubid.return_value = None

        with pytest.raises(NotFoundError, match="Group def456 not found"):
            views.reindex_group()

    def test_queue_annotaions_by_id(self, views, tasks, pyramid_request):
        pyramid_request.params = {
            "annotation_ids": """
            cdff42be-2fc0-11ef-ae06-37653ab647c1
            zf9Cvi_AEe-uBjdlOrZHwQ

            """,
            "name": "jobname",
        }

        views.queue_annotations_by_id()

        tasks.job_queue.add_annotations_by_ids.delay.assert_called_once_with(
            "jobname",
            ["zf9Cvi_AEe-uBjdlOrZHwQ", "zf9Cvi_AEe-uBjdlOrZHwQ"],
            tag="reindex_ids",
            force=False,
        )
        assert pyramid_request.session.peek_flash("success") == [
            "Began reindexing annotations by ID."
        ]

    @pytest.fixture
    def views(self, pyramid_request, queue_service):  # noqa: ARG002
        return SearchAdminViews(pyramid_request)

    @pytest.fixture(autouse=True)
    def tasks(self, patch):
        return patch("h.views.admin.search.tasks")

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("admin.search", "/admin/search")


@pytest.fixture
def group_service(pyramid_config):
    service = mock.create_autospec(GroupService, spec_set=True, instance=True)
    pyramid_config.register_service(service, name="group")
    return service

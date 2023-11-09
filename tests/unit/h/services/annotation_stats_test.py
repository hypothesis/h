from unittest import mock

import pytest

from h.search import (
    DeletedFilter,
    Limiter,
    Search,
    TopLevelAnnotationsFilter,
    UserFilter,
)
from h.services.annotation_stats import AnnotationStatsService, annotation_stats_factory


class TestAnnotationStatsService:
    def test_total_user_annotation_count_calls_search_with_request(
        self, svc, search, pyramid_request
    ):
        svc.total_user_annotation_count("userid")

        search.assert_called_with(pyramid_request)

    def test_total_user_annotation_count_calls_run_with_userid_and_limit(
        self, svc, search
    ):
        svc.total_user_annotation_count("userid")

        search.return_value.run.assert_called_with({"limit": 0, "user": "userid"})

    def test_toal_user_annotation_count_attaches_correct_modifiers(
        self, svc, search, limiter, deleted_filter, user_filter
    ):
        svc.total_user_annotation_count("userid")

        assert search.return_value.clear.called

        assert search.return_value.append_modifier.call_count == 3
        search.return_value.append_modifier.assert_has_calls(
            [
                mock.call(limiter.return_value),
                mock.call(deleted_filter.return_value),
                mock.call(user_filter.return_value),
            ]
        )

    def test_total_user_annotation_count_returns_total(self, svc, search):
        search.return_value.run.return_value.total = 3

        anns = svc.total_user_annotation_count("userid")

        assert anns == 3

    def test_user_annotation_count_calls_search_with_request(
        self, svc, search, pyramid_request
    ):
        svc.user_annotation_count("userid")

        search.assert_called_with(pyramid_request)

    def test_user_annotation_count_calls_run_with_userid_and_limit(self, svc, search):
        svc.user_annotation_count("userid")

        search.return_value.run.assert_called_with({"limit": 0, "user": "userid"})

    def test_user_annotation_count_excludes_replies(
        self, svc, search, top_level_annotation_filter
    ):
        svc.user_annotation_count("userid")

        search.return_value.append_modifier.assert_called_with(
            top_level_annotation_filter.return_value
        )

    def test_user_annotation_count_returns_total(self, svc, search):
        search.return_value.run.return_value.total = 3

        anns = svc.user_annotation_count("userid")

        assert anns == 3

    def test_group_annotation_count_calls_search_with_request(
        self, svc, search, pyramid_request
    ):
        svc.group_annotation_count("groupid")

        search.assert_called_with(pyramid_request)

    def test_group_annotation_count_calls_run_with_groupid_and_limit(self, svc, search):
        svc.group_annotation_count("groupid")

        search.return_value.run.assert_called_with({"limit": 0, "group": "groupid"})

    def test_group_annotation_count_excludes_replies(
        self, svc, search, top_level_annotation_filter
    ):
        svc.group_annotation_count("groupid")

        search.return_value.append_modifier.assert_called_with(
            top_level_annotation_filter.return_value
        )

    def test_group_annotation_count_returns_total(self, svc, search):
        search.return_value.run.return_value.total = 3

        anns = svc.group_annotation_count("groupid")

        assert anns == 3


class TestAnnotationStatsFactory:
    def test_returns_service(self):
        svc = annotation_stats_factory(mock.Mock(), mock.Mock())

        assert isinstance(svc, AnnotationStatsService)

    def test_sets_request(self):
        request = mock.Mock()
        svc = annotation_stats_factory(mock.Mock(), request)

        assert svc.request == request


@pytest.fixture
def svc(pyramid_request):
    return AnnotationStatsService(request=pyramid_request)


@pytest.fixture
def search(patch):
    return patch("h.services.annotation_stats.Search", autospec=Search, spec_set=True)


@pytest.fixture
def top_level_annotation_filter(patch):
    return patch(
        "h.services.annotation_stats.TopLevelAnnotationsFilter",
        autospec=TopLevelAnnotationsFilter,
        spec_set=True,
    )


@pytest.fixture
def limiter(patch):
    return patch("h.services.annotation_stats.Limiter", autospec=Limiter, spec_set=True)


@pytest.fixture
def deleted_filter(patch):
    return patch(
        "h.services.annotation_stats.DeletedFilter",
        autospec=DeletedFilter,
        spec_set=True,
    )


@pytest.fixture
def user_filter(patch):
    return patch(
        "h.services.annotation_stats.UserFilter", autospec=UserFilter, spec_set=True
    )

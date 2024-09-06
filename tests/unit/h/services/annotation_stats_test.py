from unittest.mock import call, sentinel

import pytest

from h.services.annotation_stats import AnnotationStatsService, annotation_stats_factory


class TestAnnotationStatsService:
    def test_user_annotation_count(
        self, pyramid_request, svc, Search, TopLevelAnnotationsFilter
    ):
        num_annotations = svc.user_annotation_count(sentinel.userid)

        Search.assert_called_with(pyramid_request)
        TopLevelAnnotationsFilter.assert_called_once_with()
        Search.return_value.append_modifier.assert_called_with(
            TopLevelAnnotationsFilter.return_value
        )
        Search.return_value.run.assert_called_with(
            {"limit": 0, "user": sentinel.userid}
        )
        assert num_annotations == Search.return_value.run.return_value.total

    def test_total_user_annotation_count(
        self, pyramid_request, svc, DeletedFilter, Limiter, Search, UserFilter
    ):
        num_annotations = svc.total_user_annotation_count(sentinel.userid)

        Search.assert_called_with(pyramid_request)
        Search.return_value.clear.assert_called_once_with()
        Limiter.assert_called_once_with()
        DeletedFilter.assert_called_once_with()
        UserFilter.assert_called_once_with()
        assert Search.return_value.append_modifier.call_args_list == [
            call(Limiter.return_value),
            call(DeletedFilter.return_value),
            call(UserFilter.return_value),
        ]
        Search.return_value.run.assert_called_with(
            {"limit": 0, "user": sentinel.userid}
        )
        assert num_annotations == Search.return_value.run.return_value.total

    def test_group_annotation_count(
        self, pyramid_request, svc, Search, TopLevelAnnotationsFilter
    ):
        num_annotations = svc.group_annotation_count(sentinel.pubid)

        Search.assert_called_with(pyramid_request)
        TopLevelAnnotationsFilter.assert_called_once_with()
        Search.return_value.append_modifier.assert_called_once_with(
            TopLevelAnnotationsFilter.return_value
        )
        Search.return_value.run.assert_called_with(
            {"limit": 0, "group": sentinel.pubid}
        )
        assert num_annotations == Search.return_value.run.return_value.total

    @pytest.mark.parametrize("unshared", [True, False])
    def test_total_group_annotation_count(
        self, pyramid_request, svc, Search, SharedAnnotationsFilter, unshared
    ):
        num_annotations = svc.total_group_annotation_count(
            sentinel.pubid, unshared=unshared
        )

        Search.assert_called_once_with(pyramid_request)
        if unshared:
            Search.return_value.append_modifier.assert_not_called()
        else:
            SharedAnnotationsFilter.assert_called_once_with()
            Search.return_value.append_modifier.assert_called_once_with(
                SharedAnnotationsFilter.return_value
            )
        Search.return_value.run.assert_called_once_with(
            {"limit": 0, "group": sentinel.pubid}
        )
        assert num_annotations == Search.return_value.run.return_value.total

    @pytest.fixture
    def svc(self, pyramid_request):
        return AnnotationStatsService(request=pyramid_request)


class TestAnnotationStatsFactory:
    def test_it(self, AnnotationStatsService):
        svc = annotation_stats_factory(sentinel.context, sentinel.request)

        AnnotationStatsService.assert_called_once_with(sentinel.request)
        assert svc == AnnotationStatsService.return_value

    @pytest.fixture(autouse=True)
    def AnnotationStatsService(self, mocker):
        return mocker.patch(
            "h.services.annotation_stats.AnnotationStatsService",
            autospec=True,
            spec_set=True,
        )


@pytest.fixture(autouse=True)
def DeletedFilter(mocker):
    return mocker.patch(
        "h.services.annotation_stats.DeletedFilter", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def Limiter(mocker):
    return mocker.patch(
        "h.services.annotation_stats.Limiter", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def Search(mocker):
    return mocker.patch(
        "h.services.annotation_stats.Search", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def SharedAnnotationsFilter(mocker):
    return mocker.patch(
        "h.services.annotation_stats.SharedAnnotationsFilter",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def TopLevelAnnotationsFilter(mocker):
    return mocker.patch(
        "h.services.annotation_stats.TopLevelAnnotationsFilter",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def UserFilter(mocker):
    return mocker.patch(
        "h.services.annotation_stats.UserFilter", autospec=True, spec_set=True
    )

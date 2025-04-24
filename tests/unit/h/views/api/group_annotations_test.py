from unittest.mock import Mock, create_autospec

import pytest
from sqlalchemy import func, select

from h.models import Annotation
from h.traversal import (
    GroupContext,
)
from h.views.api.group_annotations import list_annotations


class TestGroupAnnotations:
    def test_it(
        self,
        context,
        pyramid_request,
        AnnotationReadService,
        Pagination,
        factories,
        annotation_json_service,
        db_session,
    ):
        factories.Annotation.create_batch(3)
        db_session.flush()
        AnnotationReadService.annotation_search_query.return_value = select(Annotation)
        AnnotationReadService.count_query.return_value = select(
            func.count(Annotation.id)
        )
        Pagination.from_params.return_value = Mock(offset=0, limit=2)

        response = list_annotations(context, pyramid_request)

        Pagination.from_params.assert_called_once_with(pyramid_request.params)
        assert response == {
            "meta": {"page": {"total": 3}},
            "data": [
                annotation_json_service.present_for_user.return_value,
                annotation_json_service.present_for_user.return_value,
            ],
        }

    @pytest.fixture
    def context(self, factories):
        return create_autospec(
            GroupContext, instance=True, spec_set=True, group=factories.Group()
        )


@pytest.fixture(autouse=True)
def Pagination(mocker):
    return mocker.patch(
        "h.views.api.group_annotations.Pagination", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def AnnotationReadService(mocker):
    return mocker.patch(
        "h.views.api.group_annotations.AnnotationReadService",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def GroupMembershipJSONPresenter(mocker):
    return mocker.patch(
        "h.views.api.group_members.GroupMembershipJSONPresenter",
        autospec=True,
        spec_set=True,
    )

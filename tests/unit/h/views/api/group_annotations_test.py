from operator import attrgetter
from unittest.mock import call, create_autospec, sentinel

import pytest
from sqlalchemy import func, select

from h.models import Annotation, ModerationStatus
from h.schemas import ValidationError
from h.schemas.pagination import CursorPagination as CursorPagination_
from h.traversal import GroupContext
from h.views.api.group_annotations import list_annotations

pytestmark = pytest.mark.usefixtures("annotation_json_service")


class TestListAnnotations:
    def test_it(
        self,
        factories,
        context,
        pyramid_request,
        CursorPagination,
        FilterGroupAnnotationsSchema,
        validate_query_params,
        AnnotationReadService,
        annotation_json_service,
    ):
        annotations = factories.Annotation.create_batch(size=15)

        response = list_annotations(context, pyramid_request)

        CursorPagination.from_params.assert_called_once_with(pyramid_request.params)
        FilterGroupAnnotationsSchema.assert_called_once_with()
        validate_query_params.assert_called_once_with(
            FilterGroupAnnotationsSchema.return_value, pyramid_request.params
        )
        AnnotationReadService.annotation_search_query.assert_called_once_with(
            groupid=context.group.pubid, moderation_status=None
        )
        # It returns the annotations in reverse-chronological order of creation.
        sorted_annotations = sorted(
            annotations, key=attrgetter("created"), reverse=True
        )
        assert annotation_json_service.present_for_user.call_args_list == [
            call(annotation, pyramid_request.user) for annotation in sorted_annotations
        ]
        assert response == {
            "data": [
                # It returns the JSON presentation (the result of calling
                # AnnotationJSONService.present_for_user()) of each annotation.
                getattr(sentinel, f"annotation_json_{annotation.id}")
                for annotation in sorted_annotations
            ],
            "meta": {"page": {"total": len(annotations)}},
        }

    def test_page_size(self, factories, context, pyramid_request, CursorPagination):
        CursorPagination.from_params.return_value.size = 2
        annotations = sorted(
            factories.Annotation.create_batch(size=3),
            key=attrgetter("created"),
            reverse=True,
        )

        response = list_annotations(context, pyramid_request)

        assert response == {
            "data": [
                getattr(sentinel, f"annotation_json_{annotation.id}")
                for annotation in annotations[:2]
            ],
            "meta": {"page": {"total": len(annotations)}},
        }

    def test_cursor(self, factories, context, pyramid_request, CursorPagination):
        annotations = sorted(
            factories.Annotation.create_batch(size=5),
            key=attrgetter("created"),
            reverse=True,
        )
        CursorPagination.from_params.return_value.size = 2
        CursorPagination.from_params.return_value.after = annotations[1].created

        response = list_annotations(context, pyramid_request)

        assert response == {
            "data": [
                getattr(sentinel, f"annotation_json_{annotation.id}")
                for annotation in annotations[2:4]
            ],
            "meta": {"page": {"total": len(annotations)}},
        }

    def test_it_with_no_annotations(self, context, pyramid_request):
        response = list_annotations(context, pyramid_request)

        assert response == {"data": [], "meta": {"page": {"total": 0}}}

    @pytest.mark.parametrize(
        "moderation_status_query_param,expected_moderation_status_filter",
        [(status.name, status) for status in ModerationStatus],
    )
    def test_it_filters_by_moderation_status(
        self,
        context,
        pyramid_request,
        validate_query_params,
        AnnotationReadService,
        moderation_status_query_param,
        expected_moderation_status_filter,
    ):
        validate_query_params.return_value["moderation_status"] = (
            moderation_status_query_param
        )

        list_annotations(context, pyramid_request)

        assert (
            AnnotationReadService.annotation_search_query.call_args[1][
                "moderation_status"
            ]
            == expected_moderation_status_filter
        )

    def test_when_no_context_group(self, context, pyramid_request):
        context.group = None

        with pytest.raises(AssertionError, match="^Group is required$"):
            list_annotations(context, pyramid_request)

    def test_when_pagination_params_invalid(
        self, context, pyramid_request, CursorPagination
    ):
        CursorPagination.from_params.side_effect = ValidationError

        with pytest.raises(ValidationError):
            list_annotations(context, pyramid_request)

    def test_when_filter_params_invalid(
        self, context, pyramid_request, validate_query_params
    ):
        validate_query_params.side_effect = ValidationError

        with pytest.raises(ValidationError):
            list_annotations(context, pyramid_request)

    @pytest.fixture
    def context(self):
        return create_autospec(GroupContext, instance=True, spec_set=True)

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        # Put something (anything) in pyramid_request.params.
        # It doesn't matter to these tests what the value of
        # pyramid_request.params actually is, this is just so that the empty
        # dict {} doesn't compare equal to pyramid_request.params in assertions.
        pyramid_request.params["foo"] = sentinel.foo

        # Assign something (anything) to pyramid_request.user.
        # It doesn't matter to these tests what the value of
        # pyramid_request.user actually is, this is just so that None doesn't
        # compare equal to pyramid_request.user in assertions.
        pyramid_request.user = factories.User()

        return pyramid_request

    @pytest.fixture
    def annotation_json_service(self, annotation_json_service):
        annotation_json_service.present_for_user.side_effect = (
            lambda annotation, *_args, **_kwargs: getattr(
                sentinel, f"annotation_json_{annotation.id}"
            )
        )
        return annotation_json_service


@pytest.fixture(autouse=True)
def FilterGroupAnnotationsSchema(mocker):
    return mocker.patch(
        "h.views.api.group_annotations.FilterGroupAnnotationsSchema",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture(autouse=True)
def CursorPagination(mocker):
    CursorPagination = mocker.patch(
        "h.views.api.group_annotations.CursorPagination", autospec=True, spec_set=True
    )
    CursorPagination.from_params.return_value = CursorPagination_(size=20, after=None)
    return CursorPagination


@pytest.fixture(autouse=True)
def validate_query_params(mocker):
    return mocker.patch(
        "h.views.api.group_annotations.validate_query_params",
        autospec=True,
        spec_set=True,
        return_value={},
    )


@pytest.fixture(autouse=True)
def AnnotationReadService(mocker):
    AnnotationReadService = mocker.patch(
        "h.views.api.group_annotations.AnnotationReadService",
        autospec=True,
        spec_set=True,
    )
    AnnotationReadService.annotation_search_query.return_value = select(Annotation)
    AnnotationReadService.count_query.return_value = select(func.count(Annotation.id))
    return AnnotationReadService

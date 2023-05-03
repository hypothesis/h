from unittest import mock

import pytest
from webob.multidict import MultiDict, NestedMultiDict

from h.search.core import SearchResult
from h.traversal import AnnotationContext
from h.views.api import annotations as views
from h.views.api.exceptions import PayloadError


@pytest.mark.usefixtures("annotation_json_service", "search_lib")
class TestSearch:
    def test_it_searches(self, pyramid_request, search_lib):
        views.search(pyramid_request)

        search = search_lib.Search.return_value
        search_lib.Search.assert_called_with(pyramid_request, separate_replies=False)

        expected_params = MultiDict(
            [("sort", "updated"), ("limit", 20), ("order", "desc"), ("offset", 0)]
        )
        search.run.assert_called_once_with(expected_params)

    def test_it_presents_search_results(
        self, pyramid_request, search_run, annotation_json_service
    ):
        search_run.return_value = SearchResult(2, ["row-1", "row-2"], [], {})

        views.search(pyramid_request)

        annotation_json_service.present_all_for_user.assert_called_once_with(
            annotation_ids=["row-1", "row-2"], user=pyramid_request.user
        )

    def test_it_returns_search_results(
        self, pyramid_request, search_run, annotation_json_service
    ):
        search_run.return_value = SearchResult(2, ["row-1", "row-2"], [], {})

        expected = {
            "total": 2,
            "rows": annotation_json_service.present_all_for_user.return_value,
        }

        assert views.search(pyramid_request) == expected

    def test_it_presents_replies(
        self, pyramid_request, search_run, annotation_json_service
    ):
        pyramid_request.params = NestedMultiDict(MultiDict({"_separate_replies": "1"}))
        search_run.return_value = SearchResult(1, ["row-1"], ["reply-1", "reply-2"], {})

        views.search(pyramid_request)

        annotation_json_service.present_all_for_user.assert_called_with(
            annotation_ids=["reply-1", "reply-2"], user=pyramid_request.user
        )

    def test_it_returns_replies(
        self, pyramid_request, search_run, annotation_json_service
    ):
        pyramid_request.params = NestedMultiDict(MultiDict({"_separate_replies": "1"}))
        search_run.return_value = SearchResult(1, ["row-1"], ["reply-1", "reply-2"], {})

        expected = {
            "total": 1,
            "rows": annotation_json_service.present_all_for_user(
                annotation_ids=["row-1"], user=pyramid_request.user
            ),
            "replies": annotation_json_service.present_all_for_user(
                annotation_ids=["reply-1", "reply-2"], user=pyramid_request.user
            ),
        }

        assert views.search(pyramid_request) == expected

    @pytest.fixture
    def search_lib(self, patch):
        return patch("h.views.api.annotations.search_lib")

    @pytest.fixture
    def search_run(self, search_lib):
        return search_lib.Search.return_value.run


class TestCreate:
    def test_it(
        self,
        pyramid_request,
        CreateAnnotationSchema,
        annotation_write_service,
        annotation_json_service,
        AnnotationEvent,
    ):
        result = views.create(pyramid_request)

        # Check we validate
        CreateAnnotationSchema.assert_called_once_with(pyramid_request)
        schema = CreateAnnotationSchema.return_value
        schema.validate.assert_called_once_with(pyramid_request.json_body)
        # Check we create
        annotation_write_service.create_annotation.assert_called_once_with(
            data=schema.validate.return_value
        )
        annotation = annotation_write_service.create_annotation.return_value
        # Check the event is raised
        AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "create"
        )
        pyramid_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value
        )
        # Check we present
        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=annotation, user=pyramid_request.user
        )
        assert result == annotation_json_service.present_for_user.return_value

    @pytest.mark.usefixtures("with_invalid_json_body")
    def test_it_raises_for_invalid_json(self, pyramid_request):
        with pytest.raises(PayloadError):
            views.create(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = {}
        pyramid_request.notify_after_commit = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def CreateAnnotationSchema(self, patch):
        return patch("h.views.api.annotations.CreateAnnotationSchema")


@pytest.mark.usefixtures("annotation_json_service")
class TestRead:
    def test_it_returns_presented_annotation(
        self, annotation_json_service, pyramid_request, annotation_context
    ):
        result = views.read(annotation_context, pyramid_request)

        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=annotation_context.annotation, user=pyramid_request.user
        )
        assert result == annotation_json_service.present_for_user.return_value


@pytest.mark.usefixtures("AnnotationJSONLDPresenter", "links_service")
class TestReadJSONLD:
    def test_it_sets_correct_content_type(
        self, AnnotationJSONLDPresenter, pyramid_request
    ):
        AnnotationJSONLDPresenter.CONTEXT_URL = "http://foo.com/context.jsonld"

        context = mock.Mock()

        views.read_jsonld(context, pyramid_request)

        assert pyramid_request.response.content_type == "application/ld+json"
        assert pyramid_request.response.content_type_params == {
            "charset": "UTF-8",
            "profile": "http://foo.com/context.jsonld",
        }

    def test_it_returns_presented_annotation(
        self,
        AnnotationJSONLDPresenter,
        annotation_context,
        pyramid_request,
        links_service,
    ):
        presenter = mock.Mock()
        AnnotationJSONLDPresenter.return_value = presenter
        AnnotationJSONLDPresenter.CONTEXT_URL = "http://foo.com/context.jsonld"

        result = views.read_jsonld(annotation_context, pyramid_request)

        AnnotationJSONLDPresenter.assert_called_once_with(
            annotation_context.annotation, links_service=links_service
        )
        assert result == presenter.asdict()

    @pytest.fixture
    def AnnotationJSONLDPresenter(self, patch):
        return patch("h.views.api.annotations.AnnotationJSONLDPresenter")


class TestUpdate:
    def test_it(
        self,
        annotation_context,
        pyramid_request,
        UpdateAnnotationSchema,
        annotation_write_service,
        annotation_json_service,
        AnnotationEvent,
    ):
        returned = views.update(annotation_context, pyramid_request)

        # Check it validates the annotation
        UpdateAnnotationSchema.assert_called_once_with(
            pyramid_request,
            annotation_context.annotation.target_uri,
            annotation_context.annotation.groupid,
        )
        schema = UpdateAnnotationSchema.return_value
        # Check it updates the annotation
        schema.validate.assert_called_once_with(pyramid_request.json_body)
        annotation_write_service.update_annotation.assert_called_once_with(
            annotation_context.annotation,
            schema.validate.return_value,
        )
        # Check it publishes event
        AnnotationEvent.assert_called_once_with(
            pyramid_request,
            annotation_write_service.update_annotation.return_value.id,
            "update",
        )
        pyramid_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value
        )
        # Check it presents the annotation
        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=annotation_write_service.update_annotation.return_value,
            user=pyramid_request.user,
        )
        assert returned == annotation_json_service.present_for_user.return_value

    @pytest.mark.usefixtures("with_invalid_json_body")
    def test_it_raises_for_invalid_json(self, pyramid_request, annotation_context):
        with pytest.raises(PayloadError):
            views.update(annotation_context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = {}
        pyramid_request.notify_after_commit = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def UpdateAnnotationSchema(self, patch):
        return patch("h.views.api.annotations.UpdateAnnotationSchema")


@pytest.mark.usefixtures(
    "AnnotationEvent", "links_service", "annotation_delete_service"
)
class TestDelete:
    def test_it_calls_the_annotation_delete_service(
        self, pyramid_request, annotation_delete_service
    ):
        context = mock.Mock()

        views.delete(context, pyramid_request)

        annotation_delete_service.delete.assert_called_once_with(context.annotation)

    def test_it_returns_object(self, pyramid_request):
        context = mock.Mock()

        result = views.delete(context, pyramid_request)

        assert result == {"id": context.annotation.id, "deleted": True}


@pytest.fixture
def AnnotationEvent(patch):
    return patch("h.views.api.annotations.AnnotationEvent")


@pytest.fixture
def annotation_context(annotation):
    return AnnotationContext(annotation)


@pytest.fixture
def annotation(factories):
    return factories.Annotation()


@pytest.fixture
def with_invalid_json_body(pyramid_request):
    type(pyramid_request).json_body = None
    with mock.patch.object(
        type(pyramid_request), "json_body", new_callable=mock.PropertyMock
    ) as json_body:
        json_body.side_effect = ValueError()
        yield json_body

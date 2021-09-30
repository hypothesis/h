from unittest import mock

import pytest
from webob.multidict import MultiDict, NestedMultiDict

from h.schemas import ValidationError
from h.search.core import SearchResult
from h.services.annotation_delete import AnnotationDeleteService
from h.traversal import AnnotationContext
from h.views.api import annotations as views


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


@pytest.mark.usefixtures(
    "AnnotationEvent",
    "create_schema",
    "links_service",
    "annotation_json_service",
    "storage",
)
class TestCreate:
    def test_it(self, pyramid_request, create_schema, storage, annotation_json_service):
        result = views.create(pyramid_request)

        create_schema.assert_called_once_with(pyramid_request)
        create_schema.return_value.validate.assert_called_once_with(
            pyramid_request.json_body
        )
        storage.create_annotation.assert_called_once_with(
            pyramid_request, create_schema.return_value.validate.return_value
        )

        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=storage.create_annotation.return_value, user=pyramid_request.user
        )

        assert result == annotation_json_service.present_for_user.return_value

    def test_it_publishes_annotation_event(
        self, AnnotationEvent, pyramid_request, storage
    ):
        views.create(pyramid_request)

        annotation = storage.create_annotation.return_value
        AnnotationEvent.assert_called_once_with(
            pyramid_request, annotation.id, "create"
        )
        pyramid_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value
        )

    def test_it_raises_if_json_parsing_fails(self, pyramid_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(pyramid_request).json_body = {}
        with mock.patch.object(
            type(pyramid_request), "json_body", new_callable=mock.PropertyMock
        ) as json_body:
            json_body.side_effect = ValueError()
            with pytest.raises(views.PayloadError):
                views.create(pyramid_request)

    def test_it_raises_if_validate_raises(self, pyramid_request, create_schema):
        create_schema.return_value.validate.side_effect = ValidationError("asplode")

        with pytest.raises(ValidationError) as exc:
            views.create(pyramid_request)

        assert str(exc.value) == "asplode"

    def test_it_raises_if_create_annotation_raises(self, pyramid_request, storage):
        storage.create_annotation.side_effect = ValidationError("asplode")

        with pytest.raises(ValidationError) as exc:
            views.create(pyramid_request)

        assert str(exc.value) == "asplode"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = {}
        pyramid_request.notify_after_commit = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def create_schema(self, patch):
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


@pytest.mark.usefixtures(
    "AnnotationEvent",
    "links_service",
    "annotation_json_service",
    "update_schema",
    "storage",
)
class TestUpdate:
    def test_it(
        self,
        annotation_context,
        pyramid_request,
        update_schema,
        storage,
        annotation_json_service,
    ):
        returned = views.update(annotation_context, pyramid_request)

        update_schema.assert_called_once_with(
            pyramid_request,
            annotation_context.annotation.target_uri,
            annotation_context.annotation.groupid,
        )
        update_schema.return_value.validate.assert_called_once_with(
            pyramid_request.json_body
        )

        storage.update_annotation.assert_called_once_with(
            pyramid_request,
            annotation_context.annotation.id,
            update_schema.return_value.validate.return_value,
        )

        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=storage.update_annotation.return_value, user=pyramid_request.user
        )

        assert returned == annotation_json_service.present_for_user.return_value

    def test_it_publishes_annotation_event(
        self, annotation_context, AnnotationEvent, storage, pyramid_request
    ):
        views.update(annotation_context, pyramid_request)

        AnnotationEvent.assert_called_once_with(
            pyramid_request, storage.update_annotation.return_value.id, "update"
        )
        pyramid_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value
        )

    def test_it_raises_if_storage_raises(
        self, annotation_context, pyramid_request, storage
    ):
        storage.update_annotation.side_effect = ValidationError("asplode")

        with pytest.raises(ValidationError):
            views.update(annotation_context, pyramid_request)

    def test_it_raises_if_validate_raises(
        self, annotation_context, pyramid_request, update_schema
    ):
        update_schema.return_value.validate.side_effect = ValidationError("asplode")

        with pytest.raises(ValidationError):
            views.update(annotation_context, pyramid_request)

    def test_it_raises_if_json_parsing_fails(self, annotation_context, pyramid_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(pyramid_request).json_body = {}
        with mock.patch.object(
            type(pyramid_request), "json_body", new_callable=mock.PropertyMock
        ) as json_body:
            json_body.side_effect = ValueError()
            with pytest.raises(views.PayloadError):
                views.update(annotation_context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = {}
        pyramid_request.notify_after_commit = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def update_schema(self, patch):
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
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock(spec_set=[])
    return pyramid_request


@pytest.fixture
def storage(patch):
    return patch("h.views.api.annotations.storage")


@pytest.fixture
def annotation_delete_service(pyramid_config):
    service = mock.create_autospec(
        AnnotationDeleteService, spec_set=True, instance=True
    )
    pyramid_config.register_service(service, name="annotation_delete")
    return service

from unittest.mock import MagicMock, call, create_autospec, patch, sentinel

import pytest
from h_matchers import Any

from h.events import AnnotationEvent
from h.services.search_index import SearchIndexService, factory
from h.services.settings import SettingsService

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


class TestAddAnnotationById:
    def test_it(
        self, search_index, root_annotation, add_annotation, annotation_read_service
    ):
        annotation_read_service.get_annotation_by_id.return_value = root_annotation

        search_index.add_annotation_by_id(root_annotation.id)

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            root_annotation.id
        )

        add_annotation.assert_called_once_with(root_annotation)

    def test_it_returns_with_no_annotation(
        self, search_index, annotation_read_service, add_annotation
    ):
        annotation_read_service.get_annotation_by_id.return_value = None

        search_index.add_annotation_by_id(sentinel.any_id)

        add_annotation.assert_not_called()

    def test_it_does_nothing_if_the_annotation_is_deleted(
        self, search_index, root_annotation, mock_es_client
    ):
        root_annotation.deleted = True

        search_index.add_annotation_by_id(root_annotation.id)

        mock_es_client.conn.index.assert_not_called()

    def test_it_also_adds_the_thread_root(
        self,
        search_index,
        reply_annotation,
        root_annotation,
        annotation_read_service,
        add_annotation,
    ):
        annotation_read_service.get_annotation_by_id.side_effect = (
            reply_annotation,
            root_annotation,
        )

        search_index.add_annotation_by_id(reply_annotation.id)

        annotation_read_service.get_annotation_by_id.assert_has_calls(
            [call(reply_annotation.id), call(root_annotation.id)]
        )

        add_annotation.assert_has_calls([call(reply_annotation), call(root_annotation)])

    @pytest.fixture
    def root_annotation(self, factories):
        return factories.Annotation.build(references=[])

    @pytest.fixture
    def reply_annotation(self, factories, root_annotation):
        return factories.Annotation.build(references=[root_annotation.id])

    @pytest.fixture
    def add_annotation(self, search_index):
        # We test the behavior of add_annotation elsewhere, so we just
        # need to make sure we call it correctly
        with patch.object(search_index, "add_annotation") as add_annotation:
            yield add_annotation


class TestAddAnnotation:
    def test_it_serialises(
        self,
        search_index,
        annotation,
        pyramid_request,
        mock_es_client,
        AnnotationSearchIndexPresenter,
    ):
        search_index.add_annotation(annotation)

        AnnotationSearchIndexPresenter.assert_called_once_with(
            annotation, pyramid_request
        )
        mock_es_client.conn.index.assert_called_once_with(
            index=Any(),
            doc_type=Any(),
            body=AnnotationSearchIndexPresenter.return_value.asdict.return_value,
            id=annotation.id,
            refresh=Any(),
        )

    def test_it_calls_elasticsearch_as_expected(
        self, search_index, annotation, mock_es_client
    ):
        search_index.add_annotation(annotation)

        mock_es_client.conn.index.assert_called_once_with(
            index=mock_es_client.index,
            doc_type=mock_es_client.mapping_type,
            body=Any(),
            id=Any(),
            refresh=False,
        )

    @pytest.mark.usefixtures("with_reindex_in_progress")
    def test_it_calls_elasticsearch_again_for_a_reindex(
        self, search_index, annotation, mock_es_client
    ):
        search_index.add_annotation(annotation)

        assert mock_es_client.conn.index.call_count == 2
        mock_es_client.conn.index.assert_called_with(
            index="another_index",
            doc_type=mock_es_client.mapping_type,
            body=Any(),
            id=annotation.id,
            refresh=False,
        )

    def test_it_does_nothing_if_the_annotation_is_deleted(
        self, search_index, annotation, mock_es_client
    ):
        annotation.deleted = True

        search_index.add_annotation(annotation)

        mock_es_client.conn.index.assert_not_called()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture(autouse=True)
    def AnnotationSearchIndexPresenter(self, patch):
        return patch("h.services.search_index.AnnotationSearchIndexPresenter")


class TestDeleteAnnotationById:
    @pytest.mark.parametrize("refresh", (True, False))
    def test_delete_annotation(self, search_index, mock_es_client, refresh):
        search_index.delete_annotation_by_id(sentinel.annotation_id, refresh)

        mock_es_client.conn.index.assert_called_once_with(
            index=mock_es_client.index,
            doc_type=mock_es_client.mapping_type,
            body={"deleted": True},
            id=sentinel.annotation_id,
            refresh=refresh,
        )

    @pytest.mark.usefixtures("with_reindex_in_progress")
    @pytest.mark.parametrize("refresh", (True, False))
    def test_it_calls_elasticsearch_again_for_a_reindex(
        self, search_index, mock_es_client, refresh
    ):
        search_index.delete_annotation_by_id(sentinel.annotation_id, refresh)

        assert mock_es_client.conn.index.call_count == 2
        mock_es_client.conn.index.assert_called_with(
            index="another_index",
            doc_type=mock_es_client.mapping_type,
            body=Any(),
            id=sentinel.annotation_id,
            refresh=refresh,
        )


class TestHandleAnnotationEvent:
    def test_we_dispatch_correctly(
        self, search_index, pyramid_request, action, handler_for
    ):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, action)

        result = search_index.handle_annotation_event(event)

        handler = handler_for(action, synchronous=True)
        handler.assert_called_once_with(event.annotation_id)
        assert result == handler.return_value

    def test_we_do_nothing_for_unexpected_actions(self, search_index, pyramid_request):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, "strange_action")

        result = search_index.handle_annotation_event(event)

        assert not result

    def test_we_fallback_to_async_if_sync_fails(
        self, search_index, pyramid_request, action, handler_for
    ):
        event = AnnotationEvent(pyramid_request, {"id": "any"}, action)
        sync_handler = handler_for(action, synchronous=True)
        sync_handler.side_effect = ValueError

        result = search_index.handle_annotation_event(event)

        sync_handler.assert_called_once_with(event.annotation_id)
        async_handler = handler_for(action, synchronous=False)
        async_handler.assert_called_once_with(event.annotation_id)
        assert result == async_handler.return_value

    @pytest.fixture(autouse=True)
    def handler_for(self, add_annotation_by_id, delete_annotation_by_id, tasks):
        handler_map = {
            True: {
                "create": add_annotation_by_id,
                "update": add_annotation_by_id,
                "delete": delete_annotation_by_id,
            },
            False: {
                "create": tasks.indexer.add_annotation.delay,
                "update": tasks.indexer.add_annotation.delay,
                "delete": tasks.indexer.delete_annotation.delay,
            },
        }

        def handler_for(action, synchronous):
            return handler_map[synchronous].get(action)

        return handler_for

    @pytest.fixture(params=("create", "update", "delete"))
    def action(self, request):
        return request.param

    @pytest.fixture(autouse=True)
    def add_annotation_by_id(self, search_index):
        with patch.object(search_index, "add_annotation_by_id") as add_annotation_by_id:
            yield add_annotation_by_id

    @pytest.fixture(autouse=True)
    def delete_annotation_by_id(self, search_index):
        with patch.object(
            search_index, "delete_annotation_by_id"
        ) as delete_annotation_by_id:
            yield delete_annotation_by_id


class TestFactory:
    def test_it(
        self, pyramid_request, SearchIndexService, settings, annotation_read_service
    ):
        result = factory(sentinel.context, pyramid_request)

        SearchIndexService.assert_called_once_with(
            request=pyramid_request,
            es=pyramid_request.es,
            settings=settings,
            annotation_read_service=annotation_read_service,
        )
        assert result == SearchIndexService.return_value

    @pytest.fixture
    def settings(self, pyramid_config):
        settings = sentinel.settings
        pyramid_config.register_service(settings, name="settings")
        return settings

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.es = sentinel.es
        return pyramid_request

    @pytest.fixture(autouse=True)
    def SearchIndexService(self, patch):
        return patch("h.services.search_index.SearchIndexService")


@pytest.fixture
def with_reindex_in_progress(settings_service):
    settings_service.get.side_effect = {
        SearchIndexService.REINDEX_SETTING_KEY: "another_index"
    }.get


@pytest.fixture
def settings_service(pyramid_config):
    settings_service = create_autospec(SettingsService)
    settings_service.get.return_value = False

    pyramid_config.register_service(settings_service, name="settings")
    return settings_service


@pytest.fixture
def search_index(
    mock_es_client,
    pyramid_request,
    settings_service,
    annotation_read_service,
):
    return SearchIndexService(
        request=pyramid_request,
        es=mock_es_client,
        settings=settings_service,
        annotation_read_service=annotation_read_service,
    )


@pytest.fixture(autouse=True)
def tasks(patch):
    return patch("h.services.search_index.tasks")


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("h.services.search_index.report_exception")


@pytest.fixture
def mock_es_client(mock_es_client):
    # The ES library uses some fancy decorators which confuse autospeccing
    mock_es_client.conn.index = MagicMock()

    return mock_es_client

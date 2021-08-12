import datetime
from unittest.mock import call, create_autospec, patch, sentinel

import pytest
from h_matchers import Any

from h.events import AnnotationEvent
from h.search.client import Client
from h.services.search_index._queue import Queue
from h.services.search_index.service import SearchIndexService
from h.services.settings import SettingsService


class TestAddAnnotationById:
    def test_it(self, search_index, root_annotation, storage, add_annotation):
        storage.fetch_annotation.return_value = root_annotation

        search_index.add_annotation_by_id(root_annotation.id)

        storage.fetch_annotation.assert_called_once_with(
            search_index._db, root_annotation.id  # pylint:disable=protected-access
        )

        add_annotation.assert_called_once_with(root_annotation)

    def test_it_returns_with_no_annotation(self, search_index, storage, add_annotation):
        storage.fetch_annotation.return_value = None

        search_index.add_annotation_by_id(sentinel.any_id)

        add_annotation.assert_not_called()

    def test_it_does_nothing_if_the_annotation_is_deleted(
        self, search_index, root_annotation, es_client
    ):
        root_annotation.deleted = True

        search_index.add_annotation_by_id(root_annotation.id)

        es_client.conn.index.assert_not_called()

    def test_it_also_adds_the_thread_root(
        self, search_index, reply_annotation, root_annotation, storage, add_annotation
    ):
        storage.fetch_annotation.side_effect = [reply_annotation, root_annotation]

        search_index.add_annotation_by_id(reply_annotation.id)

        storage.fetch_annotation.assert_has_calls(
            # pylint:disable=protected-access
            [
                call(search_index._db, reply_annotation.id),
                call(search_index._db, root_annotation.id),
            ]
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
        es_client,
        AnnotationSearchIndexPresenter,
    ):
        search_index.add_annotation(annotation)

        AnnotationSearchIndexPresenter.assert_called_once_with(
            annotation, pyramid_request
        )
        es_client.conn.index.assert_called_once_with(
            index=Any(),
            doc_type=Any(),
            body=AnnotationSearchIndexPresenter.return_value.asdict.return_value,
            id=annotation.id,
            refresh=Any(),
        )

    def test_it_calls_elasticsearch_as_expected(
        self, search_index, annotation, es_client
    ):
        search_index.add_annotation(annotation)

        es_client.conn.index.assert_called_once_with(
            index=es_client.index,
            doc_type=es_client.mapping_type,
            body=Any(),
            id=Any(),
            refresh=False,
        )

    @pytest.mark.usefixtures("with_reindex_in_progress")
    def test_it_calls_elasticsearch_again_for_a_reindex(
        self, search_index, annotation, es_client
    ):
        search_index.add_annotation(annotation)

        assert es_client.conn.index.call_count == 2
        es_client.conn.index.assert_called_with(
            index="another_index",
            doc_type=es_client.mapping_type,
            body=Any(),
            id=annotation.id,
            refresh=False,
        )

    def test_it_does_nothing_if_the_annotation_is_deleted(
        self, search_index, annotation, es_client
    ):
        annotation.deleted = True

        search_index.add_annotation(annotation)

        es_client.conn.index.assert_not_called()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()


class TestAddAnnotationsBetweenTimes:
    def test_it(self, indexer, search_index):
        start_time = datetime.datetime(2020, 9, 9)
        end_time = datetime.datetime(2020, 9, 11)

        search_index.add_annotations_between_times(
            start_time,
            end_time,
            "test_tag",
        )

        indexer.add_annotations_between_times.delay.assert_called_once_with(
            start_time, end_time, "test_tag"
        )


class TestAddUsersAnnotations:
    def test_it(self, indexer, search_index):
        search_index.add_users_annotations(
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        indexer.add_users_annotations.delay.assert_called_once_with(
            sentinel.userid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


class TestAddGroupAnnotations:
    def test_it(self, indexer, search_index):
        search_index.add_group_annotations(
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )

        indexer.add_group_annotations.delay.assert_called_once_with(
            sentinel.groupid,
            sentinel.tag,
            force=sentinel.force,
            schedule_in=sentinel.schedule_in,
        )


class TestDeleteAnnotationById:
    @pytest.mark.parametrize("refresh", (True, False))
    def test_delete_annotation(self, search_index, es_client, refresh):
        search_index.delete_annotation_by_id(sentinel.annotation_id, refresh)

        es_client.conn.index.assert_called_once_with(
            index=es_client.index,
            doc_type=es_client.mapping_type,
            body={"deleted": True},
            id=sentinel.annotation_id,
            refresh=refresh,
        )

    @pytest.mark.usefixtures("with_reindex_in_progress")
    @pytest.mark.parametrize("refresh", (True, False))
    def test_it_calls_elasticsearch_again_for_a_reindex(
        self, search_index, es_client, refresh
    ):
        search_index.delete_annotation_by_id(sentinel.annotation_id, refresh)

        assert es_client.conn.index.call_count == 2
        es_client.conn.index.assert_called_with(
            index="another_index",
            doc_type=es_client.mapping_type,
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
    def handler_for(self, add_annotation_by_id, delete_annotation_by_id, indexer):
        handler_map = {
            True: {
                "create": add_annotation_by_id,
                "update": add_annotation_by_id,
                "delete": delete_annotation_by_id,
            },
            False: {
                "create": indexer.add_annotation.delay,
                "update": indexer.add_annotation.delay,
                "delete": indexer.delete_annotation.delay,
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


class TestSync:
    def test_it(self, search_index, queue):
        returned = search_index.sync(10)

        queue.sync.assert_called_once_with(10)
        assert returned == queue.sync.return_value


@pytest.fixture(autouse=True)
def AnnotationSearchIndexPresenter(patch):
    return patch("h.services.search_index.service.AnnotationSearchIndexPresenter")


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
def queue():
    return create_autospec(Queue, spec_set=True, instance=True)


@pytest.fixture
def search_index(es_client, pyramid_request, settings_service, queue):
    return SearchIndexService(
        session=pyramid_request.db,
        es_client=es_client,
        request=pyramid_request,
        settings=settings_service,
        queue=queue,
    )


@pytest.fixture(autouse=True)
def es_client():
    return create_autospec(Client, instance=True)


@pytest.fixture(autouse=True)
def indexer(patch):
    return patch("h.services.search_index.service.indexer")


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("h.services.search_index.service.report_exception")


@pytest.fixture(autouse=True)
def storage(patch):
    return patch("h.services.search_index.service.storage")

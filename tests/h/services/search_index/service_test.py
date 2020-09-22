from unittest.mock import create_autospec, patch, sentinel

import pytest
from h_matchers import Any

from h.search.client import Client
from h.services.search_index.service import SearchIndexService
from h.services.settings import SettingsService


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

    def test_it_notifies_of_annotation_transformation(
        self,
        search_index,
        annotation,
        pyramid_request,
        AnnotationTransformEvent,
        AnnotationSearchIndexPresenter,
    ):
        with patch.object(pyramid_request, "registry") as registry:
            search_index.add_annotation(annotation)

            AnnotationTransformEvent.assert_called_once_with(
                pyramid_request,
                annotation,
                AnnotationSearchIndexPresenter.return_value.asdict.return_value,
            )
            registry.notify.assert_called_once_with(
                AnnotationTransformEvent.return_value
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

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture(autouse=True)
    def AnnotationTransformEvent(self, patch):
        return patch("h.services.search_index.service.AnnotationTransformEvent")

    @pytest.fixture(autouse=True)
    def AnnotationSearchIndexPresenter(self, patch):
        return patch("h.services.search_index.service.AnnotationSearchIndexPresenter")


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
def search_index(es_client, pyramid_request, settings_service):
    return SearchIndexService(es_client, pyramid_request, settings_service)


@pytest.fixture(autouse=True)
def es_client():
    return create_autospec(Client, instance=True)

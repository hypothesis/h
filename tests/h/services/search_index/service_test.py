from unittest.mock import create_autospec, patch, sentinel

import pytest
from h_matchers import Any

from h.search.client import Client
from h.services.search_index.service import SearchIndexService


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

    @pytest.mark.parametrize("target_index", (None, "another"))
    def test_it_calls_elasticsearch_as_expected(
        self, search_index, annotation, target_index, es_client
    ):
        search_index.add_annotation(annotation, target_index=target_index)

        es_client.conn.index.assert_called_once_with(
            index=es_client.index if target_index is None else target_index,
            doc_type=es_client.mapping_type,
            body=Any(),
            id=Any(),
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
    @pytest.mark.parametrize("target_index", (None, "another"))
    @pytest.mark.parametrize("refresh", (True, False))
    def test_delete_annotation(self, search_index, es_client, target_index, refresh):
        search_index.delete_annotation_by_id(
            sentinel.annotation_id, target_index, refresh
        )

        es_client.conn.index.assert_called_once_with(
            index=es_client.index if target_index is None else target_index,
            doc_type=es_client.mapping_type,
            body={"deleted": True},
            id=sentinel.annotation_id,
            refresh=refresh,
        )


@pytest.fixture
def search_index(es_client, pyramid_request):
    return SearchIndexService(es_client, pyramid_request)


@pytest.fixture(autouse=True)
def es_client():
    return create_autospec(Client, instance=True)

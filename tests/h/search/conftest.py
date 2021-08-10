from unittest import mock

import pytest

from h.services.group import GroupService
from h.services.search_index import SearchIndexService
from h.services.search_index._queue import Queue


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.create_autospec(GroupService, instance=True, spec_set=True)
    group_service.groupids_readable_by.return_value = ["__world__"]
    pyramid_config.register_service(group_service, name="group")
    return group_service


@pytest.fixture
def Annotation(factories, index_annotations):
    """
    Create and index an annotation.

    Looks like factories.Annotation() but automatically uses the build()
    strategy and automatically indexes the annotation into the test
    Elasticsearch index.
    """

    def _Annotation(**kwargs):
        annotation = factories.Annotation.build(**kwargs)
        index_annotations(annotation)
        return annotation

    return _Annotation


@pytest.fixture
def index_annotations(es_client, search_index):
    def _index(*annotations):
        """Index the given annotation(s) into Elasticsearch."""
        for annotation in annotations:
            search_index.add_annotation(annotation)

        es_client.conn.indices.refresh(index=es_client.index)

    return _index


@pytest.fixture
def search_index(  # pylint:disable=unused-argument
    es_client, pyramid_request, moderation_service
):
    return SearchIndexService(
        pyramid_request,
        es_client,
        session=pyramid_request.db,
        settings={},
        queue=mock.create_autospec(Queue, spec_set=True, instance=True),
    )


@pytest.fixture
def pyramid_request(es_client, pyramid_request):
    pyramid_request.es = es_client
    return pyramid_request

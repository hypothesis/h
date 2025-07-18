from unittest import mock

import pytest

from h.models import Group
from h.services.group import GroupService
from h.services.search_index import SearchIndexService


@pytest.fixture
def world_group(db_session):
    return db_session.query(Group).filter_by(pubid="__world__").one()


@pytest.fixture
def group_service(pyramid_config, world_group):
    group_service = mock.create_autospec(GroupService, instance=True, spec_set=True)
    group_service.groups_readable_by.return_value = [world_group]
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
def search_index(
    es_client,
    pyramid_request,
    moderation_service,  # noqa: ARG001
    annotation_read_service,
):
    return SearchIndexService(
        pyramid_request,
        es=es_client,
        settings={},
        annotation_read_service=annotation_read_service,
    )


@pytest.fixture
def pyramid_request(es_client, pyramid_request):
    pyramid_request.es = es_client
    return pyramid_request

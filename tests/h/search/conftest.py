# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

import h.search.index
from h.services.group import GroupService
from h.services.annotation_moderation import AnnotationModerationService


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.create_autospec(GroupService, instance=True, spec_set=True)
    group_service.groupids_readable_by.return_value = ["__world__"]
    pyramid_config.register_service(group_service, name="group")
    return group_service


@pytest.fixture
def moderation_service(pyramid_config):
    svc = mock.create_autospec(
        AnnotationModerationService, spec_set=True, instance=True
    )
    svc.all_hidden.return_value = []
    pyramid_config.register_service(svc, name="annotation_moderation")
    return svc


@pytest.fixture
def Annotation(factories, index):
    """Create and index an annotation.

    Looks like factories.Annotation() but automatically uses the build()
    strategy and automatically indexes the annotation into the test
    Elasticsearch index.
    """

    def _Annotation(**kwargs):
        annotation = factories.Annotation.build(**kwargs)
        index(annotation)
        return annotation

    return _Annotation


@pytest.fixture
def index(es_client, pyramid_request, moderation_service):
    def _index(*annotations):
        """Index the given annotation(s) into Elasticsearch."""
        for annotation in annotations:
            h.search.index.index(es_client, annotation, pyramid_request)
        es_client.conn.indices.refresh(index=es_client.index)

    return _index


@pytest.fixture
def pyramid_request(es_client, pyramid_request):
    pyramid_request.es = es_client
    return pyramid_request

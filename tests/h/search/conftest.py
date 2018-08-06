# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

import h.search.index
from h.services.group import GroupService


@pytest.fixture(autouse=True)
def group_service(pyramid_config):
    group_service = mock.create_autospec(GroupService, instance=True, spec_set=True)
    group_service.groupids_readable_by.return_value = ["__world__"]
    pyramid_config.register_service(group_service, name="group")
    return group_service


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
def index(es6_client, pyramid_request):
    def _index(*annotations):
        """Index the given annotation(s) into Elasticsearch."""
        for annotation in annotations:
            h.search.index.index(es6_client, annotation, pyramid_request)
        es6_client.conn.indices.refresh(index=es6_client.index)

    return _index


@pytest.fixture
def pyramid_request(es6_client, pyramid_request):
    pyramid_request.es = es6_client
    return pyramid_request

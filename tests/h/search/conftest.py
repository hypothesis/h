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
def index(es_client, pyramid_request):
    def _index(*annotations):
        """Index the given annotation(s) into Elasticsearch."""
        for annotation in annotations:
            h.search.index.index(es_client, annotation, pyramid_request)
        es_client.conn.indices.refresh(index=es_client.index)
    return _index

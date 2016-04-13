# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

import elasticsearch

from h.api.search import client
from h.api.search import index


@pytest.mark.usefixtures('presenters')
class TestIndexAnnotation:

    def test_it_presents_the_annotation(self, es, presenters):
        request = mock.Mock()
        annotation = mock.Mock()

        index.index(es, annotation, request)

        presenters.AnnotationJSONPresenter.assert_called_once_with(
            request, annotation)

    def test_it_indexes_the_annotation(self, es, presenters):
        index.index(es, mock.Mock(), mock.Mock())

        es.conn.index.assert_called_once_with(
            index='hypothesis',
            doc_type='annotation',
            body=presenters.AnnotationJSONPresenter.return_value.asdict.return_value,
            id='test_annotation_id',
        )

    def test_it_inserts_the_source_field(self, es):
        annotation = mock.Mock()

        index.index(es, annotation, mock.Mock())

        assert es.conn.index.call_args[1]['body']['target'][0]['scope'] == [annotation.target_uri_normalized]

    @pytest.fixture
    def presenters(self, patch):
        presenters = patch('h.api.search.index.presenters')
        presenter = presenters.AnnotationJSONPresenter.return_value
        presenter.asdict.return_value = {
            'id': 'test_annotation_id',
            'target': [
                {
                    'source': 'http://example.com/example',
                },
            ],
        }
        return presenters


@pytest.fixture
def es():
    mock_es = mock.Mock(spec=client.Client('localhost', 'hypothesis'))
    mock_es.index = 'hypothesis'
    mock_es.t.annotation = 'annotation'
    return mock_es

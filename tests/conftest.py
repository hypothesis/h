# -*- coding: utf-8 -*-

import os

import pytest
from webtest import TestApp

TEST_SETTINGS = {
    'es.host': os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200'),
    'es.index': 'hypothesis-test',
    'legacy.es.index': 'annotator-test',
    'h.db.should_create_all': True,
    'h.db.should_drop_all': True,
    'h.search.autoconfig': True,
    'pyramid.includes': 'h.session',
    'sqlalchemy.url': os.environ.get('TEST_DATABASE_URL',
                                     'postgresql://postgres@localhost/htest')
}


@pytest.fixture
def config():
    from h.config import configure
    _drop_indices(settings=TEST_SETTINGS)
    config = configure(settings=TEST_SETTINGS)
    config.include('h.app')
    return config


@pytest.fixture
def app(config):
    return TestApp(config.make_wsgi_app())


def _drop_indices(settings):
    import elasticsearch

    conn = elasticsearch.Elasticsearch([settings['es.host']])

    for name in [settings['es.index'], settings['legacy.es.index']]:
        if conn.indices.exists(index=name):
            conn.indices.delete(index=name)

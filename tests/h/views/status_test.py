# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.exceptions import APIError
from h.views.status import status


@pytest.mark.usefixtures('celery', 'db', 'es')
class TestStatus(object):
    def test_it_returns_okay_on_success(self, pyramid_request):
        result = status(pyramid_request)
        assert result

    def test_it_fails_when_databse_unreachable(self, pyramid_request, db):
        db.execute.side_effect = Exception('explode!')

        with pytest.raises(APIError) as exc:
            status(pyramid_request)

        assert 'Database connection failed' in exc.value.message

    def test_it_fails_when_search_unreachable(self, pyramid_request, es):
        es.conn.cluster.health.side_effect = Exception('explode!')

        with pytest.raises(APIError) as exc:
            status(pyramid_request)

        assert 'Search connection failed' in exc.value.message

    def test_it_fails_when_search_cluster_status_red(self, pyramid_request, es):
        es.conn.cluster.health.return_value = {'status': 'red'}

        with pytest.raises(APIError) as exc:
            status(pyramid_request)

        assert 'Search connection failed' in exc.value.message

    def test_it_fails_when_celery_connection_unreachable(self, pyramid_request, celery):
        celery.control.ping.side_effect = IOError('explode!')

        with pytest.raises(APIError) as exc:
            status(pyramid_request)

        assert 'Celery connection failed' in exc.value.message

    def test_it_fails_when_celery_workers_dont_respond(self, pyramid_request, celery):
        celery.control.ping.return_value = []

        with pytest.raises(APIError) as exc:
            status(pyramid_request)

        assert 'Celery ping failed' in exc.value.message

    def test_it_succeeds_when_one_celery_workers_succeeds(self, pyramid_request, celery):
        celery.control.ping.return_value = [
            {'celery@test-worker-1': {'fail': 'some error'}},
            {'celery@test-worker-2': {'ok': 'pong'}},
        ]

        result = status(pyramid_request)
        assert result

    def test_it_fails_when_all_celery_workers_fail(self, pyramid_request, celery):
        celery.control.ping.return_value = [
            {'celery@test-worker-1': {'fail': 'some error'}},
            {'celery@test-worker-2': {'foo': 'bar'}},
        ]

        with pytest.raises(APIError) as exc:
            status(pyramid_request)

        assert 'no worker returned pong' in exc.value.message

    @pytest.fixture
    def db(self, pyramid_request):
        db = mock.Mock()
        pyramid_request.db = db
        return db

    @pytest.fixture
    def es(self, pyramid_request):
        es = mock.Mock()
        es.conn.cluster.health.return_value = {'status': 'green'}
        pyramid_request.es = es
        return es

    @pytest.fixture
    def celery(self, patch):
        celery = patch('h.views.status.celery')

        celery.control.ping.return_value = [{'celery@test-worker': {'ok': 'pong'}}]

        return celery

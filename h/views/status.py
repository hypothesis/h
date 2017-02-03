# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from h.celery import celery
from h.exceptions import APIError
from h.util.view import json_view


log = logging.getLogger(__name__)


@json_view(route_name='status')
def status(request):
    _check_database(request)
    _check_search(request)
    _check_celery()
    return {'status': 'okay'}


def _check_database(request):
    try:
        request.db.execute('SELECT 1')
    except Exception as exc:
        log.exception(exc)
        raise APIError('Database connection failed')


def _check_search(request):
    try:
        info = request.es.conn.cluster.health()
        if info['status'] not in ('green', 'yellow'):
            raise APIError('Search cluster state is %s' % info['status'])
    except Exception as exc:
        log.exception(exc)
        raise APIError('Search connection failed')


def _check_celery():
    try:
        result = celery.control.ping(timeout=0.25)
        if not result:
            raise APIError('Celery ping failed')

        for item in result:
            if len(item) != 1:
                continue

            reply = item.values()[0]
            if reply.get('ok') == 'pong':
                return

        raise APIError('Celery: no worker returned pong')
    except IOError as exc:
        log.exception(exc)
        raise APIError('Celery connection failed')

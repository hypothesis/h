# -*- coding: utf-8 -*-
import os
from mock import patch
from h.config import settings_from_environment


@patch.dict(os.environ)
def test_es_environment():
    os.environ['ELASTICSEARCH_PORT'] = 'tcp://127.0.0.1:1234'
    os.environ['ELASTICSEARCH_PORT_9200_TCP_ADDR'] = '127.0.0.1'
    os.environ['ELASTICSEARCH_PORT_9200_TCP_PORT'] = '1234'
    os.environ['ELASTICSEARCH_INDEX'] = 'new-index'

    actual_config = settings_from_environment()
    expected_config = {
        'es.host': 'http://127.0.0.1:1234',
        'es.index': 'new-index',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_mail_environment():
    os.environ['MAIL_PORT'] = 'tcp://127.0.0.1:4567'
    os.environ['MAIL_PORT_25_TCP_ADDR'] = '127.0.0.1'
    os.environ['MAIL_PORT_25_TCP_PORT'] = '4567'

    actual_config = settings_from_environment()
    expected_config = {
        'mail.host': '127.0.0.1',
        'mail.port': '4567',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_sqlite_database_environment():
    os.environ['DATABASE_URL'] = 'sqlite:///tmp/database.db'

    actual_config = settings_from_environment()
    expected_config = {'sqlalchemy.url': 'sqlite:///tmp/database.db'}
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_postgres_database_environment():
    os.environ['DATABASE_URL'] = 'postgres://postgres:1234/database'

    actual_config = settings_from_environment()
    expected_config = {
        'sqlalchemy.url': 'postgresql+psycopg2://postgres:1234/database'
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_redis_database_environment():
    os.environ['REDIS_PORT'] = 'tcp://127.0.0.1:4567'
    os.environ['REDIS_PORT_6379_TCP_ADDR'] = '127.0.0.1'
    os.environ['REDIS_PORT_6379_TCP_PORT'] = '4567'

    actual_config = settings_from_environment()
    expected_config = {
        'redis.sessions.host': '127.0.0.1',
        'redis.sessions.port': '4567',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_session_secret_environment():
    os.environ['SESSION_SECRET'] = 's3kr1t'

    actual_config = settings_from_environment()
    expected_config = {
        'session.secret': 's3kr1t',
        'redis.sessions.secret': 's3kr1t',
    }
    assert actual_config == expected_config

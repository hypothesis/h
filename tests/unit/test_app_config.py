import os
import elasticsearch
from mock import patch, call
from pyramid.paster import get_appsettings
from h import main

@patch('h.create_app')
@patch.dict(os.environ)
def test_es_environment_overrides(create_app):
    os.environ['ELASTICSEARCH_PORT'] = 'tcp://127.0.0.1:1234'
    os.environ['ELASTICSEARCH_INDEX'] = 'new-index'

    app = main({})
    expected_config = {
        'es.host': 'http://127.0.0.1:1234',
        'es.index': 'new-index',
    }
    assert create_app.mock_calls == [call(expected_config)]

@patch('h.create_app')
@patch.dict(os.environ)
def test_mail_environment_overrides(create_app):
    os.environ['MAIL_PORT'] = 'tcp://127.0.0.1:4567'

    app = main({})
    expected_config = {
        'mail.host': '127.0.0.1',
        'mail.port': '4567',
    }
    assert create_app.mock_calls == [call(expected_config)]

@patch('h.create_app')
@patch.dict(os.environ)
def test_sqlite_database_environment_overrides(create_app):
    os.environ['DATABASE_URL'] = 'sqlite:///tmp/database.db'

    app = main({})
    expected_config = {'sqlalchemy.url': 'sqlite:///tmp/database.db'}
    assert create_app.mock_calls == [call(expected_config)]

@patch('h.create_app')
@patch.dict(os.environ)
def test_postgres_database_environment_overrides(create_app):
    os.environ['DATABASE_URL'] = 'postgres://postgres:1234/database'

    app = main({})
    expected_config = {'sqlalchemy.url': 'postgres+psycopg2://postgres:1234/database'}
    assert create_app.mock_calls == [call(expected_config)]

@patch('h.create_app')
@patch.dict(os.environ)
def test_global_config_precence(create_app):
    os.environ['DATABASE_URL'] = 'postgres://postgres:1234/database'

    app = main({'sqlalchemy.url': 'postgres://localhost:5000'})
    expected_config = {'sqlalchemy.url': 'postgres://localhost:5000'}
    assert create_app.mock_calls == [call(expected_config)]

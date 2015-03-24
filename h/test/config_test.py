# -*- coding: utf-8 -*-
import os
from mock import patch
from h.config import settings_from_environment


@patch.dict(os.environ)
def test_heroku_bonsai():
    url = 'http://ql9lsrn8:img5ndnsbtaahloy@redwood-94865.us-east-1.bonsai.io/'
    os.environ['BONSAI_URL'] = url

    actual_config = settings_from_environment()
    expected_config = {
        'es.host': url,
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_heroku_redistogo():
    url = 'redis://redistogo:12345@mummichog.redistogo.com:9128/'
    os.environ['REDISTOGO_URL'] = url

    actual_config = settings_from_environment()
    expected_config = {
        'redis.sessions.url': url + '0',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_heroku_database_sqlite():
    os.environ['DATABASE_URL'] = 'sqlite:///tmp/database.db'

    actual_config = settings_from_environment()
    expected_config = {'sqlalchemy.url': 'sqlite:///tmp/database.db'}
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_heroku_database_postgres():
    os.environ['DATABASE_URL'] = 'postgres://postgres:1234/database'

    actual_config = settings_from_environment()
    expected_config = {
        'sqlalchemy.url': 'postgresql+psycopg2://postgres:1234/database'
    }
    assert actual_config == expected_config


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
def test_mail_mailgun():
    os.environ['MAILGUN_SMTP_LOGIN'] = 'hollywood'
    os.environ['MAILGUN_SMTP_PASSWORD'] = 'wolfman'

    actual_config = settings_from_environment()
    expected_config = {
        'mail.username': 'hollywood',
        'mail.password': 'wolfman',
        'mail.host': 'smtp.mailgun.org',
        'mail.port': 587,
        'mail.tls': True,
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_mail_mandrill():
    os.environ['MANDRILL_USERNAME'] = 'maverick'
    os.environ['MANDRILL_APIKEY'] = 'ace'

    actual_config = settings_from_environment()
    expected_config = {
        'mail.username': 'maverick',
        'mail.password': 'ace',
        'mail.host': 'smtp.mandrillapp.com',
        'mail.port': 587,
        'mail.tls': True,
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_mail_sendgrid():
    os.environ['SENDGRID_USERNAME'] = 'goose'
    os.environ['SENDGRID_PASSWORD'] = 'stud'

    actual_config = settings_from_environment()
    expected_config = {
        'mail.username': 'goose',
        'mail.password': 'stud',
        'mail.host': 'smtp.sendgrid.net',
        'mail.port': 587,
        'mail.tls': True,
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_mail_sender():
    os.environ['MAIL_DEFAULT_SENDER'] = 'zardoz@vortex.org'

    actual_config = settings_from_environment()
    expected_config = {
        'mail.default_sender': 'zardoz@vortex.org',
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
def test_nsqd_environment():
    os.environ['NSQD_PORT'] = 'tcp://127.0.0.1:4150'
    os.environ['NSQD_PORT_4150_TCP_ADDR'] = 'tcp.nsqd.local'
    os.environ['NSQD_PORT_4150_TCP_PORT'] = '4150'
    os.environ['NSQD_PORT_4151_TCP_ADDR'] = 'http.nsqd.local'
    os.environ['NSQD_PORT_4151_TCP_PORT'] = '4151'

    actual_config = settings_from_environment()
    expected_config = {
        'nsq.reader.addresses': 'tcp.nsqd.local:4150',
        'nsq.writer.address': 'http.nsqd.local:4151',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_nsq_namespace():
    os.environ['NSQ_NAMESPACE'] = 'staging'

    actual_config = settings_from_environment()
    expected_config = {
        'nsq.namespace': 'staging',
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
def test_client_credentials_environment():
    os.environ['CLIENT_ID'] = 'annotate'
    os.environ['CLIENT_SECRET'] = 'unsecret'

    actual_config = settings_from_environment()
    expected_config = {
        'h.client_id': 'annotate',
        'h.client_secret': 'unsecret',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_secret_key_environment():
    os.environ['SECRET_KEY'] = 's3kr1t'

    actual_config = settings_from_environment()
    expected_config = {
        'secret_key': 's3kr1t',
    }
    assert actual_config == expected_config


@patch.dict(os.environ)
def test_session_secret_environment():  # bw compat
    os.environ['SESSION_SECRET'] = 's3kr1t'

    actual_config = settings_from_environment()
    expected_config = {
        'secret_key': 's3kr1t',
    }
    assert actual_config == expected_config

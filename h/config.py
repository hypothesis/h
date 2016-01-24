# -*- coding: utf-8 -*-
import os
import logging

from pyramid.settings import asbool

from h._compat import urlparse

log = logging.getLogger(__name__)


def settings_from_environment():
    settings = {}

    _setup_analytics(settings)
    _setup_auth_domain(settings)
    _setup_heroku(settings)
    _setup_db(settings)
    _setup_elasticsearch(settings)
    _setup_email(settings)
    _setup_nsqd(settings)
    _setup_redis(settings)
    _setup_secrets(settings)
    _setup_client(settings)
    _setup_statsd(settings)
    _setup_webassets(settings)
    _setup_websocket(settings)

    return settings


def normalize_database_url(url):
    # Heroku database URLs start with postgres://, which is an old and
    # deprecated dialect as far as sqlalchemy is concerned. We upgrade this
    # to postgresql+psycopg2 by default.
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg2://' + url[len('postgres://'):]
    return url


def _setup_analytics(settings):
    if 'GOOGLE_ANALYTICS_TRACKING_ID' in os.environ:
        settings['ga_tracking_id'] = os.environ['GOOGLE_ANALYTICS_TRACKING_ID']


def _setup_auth_domain(settings):
    if 'AUTH_DOMAIN' in os.environ:
        settings['h.auth_domain'] = os.environ['AUTH_DOMAIN']


def _setup_heroku(settings):
    # BONSAI_URL matches the Heroku environment variable for the Bonsai add-on
    if 'BONSAI_URL' in os.environ:
        settings['es.host'] = os.environ['BONSAI_URL']

    # DATABASE_URL matches the Heroku environment variable
    if 'DATABASE_URL' in os.environ:
        settings['sqlalchemy.url'] = normalize_database_url(
            os.environ['DATABASE_URL'])

    # REDISTOGO_URL matches the Heroku environment variable for Redis To Go
    if 'REDISTOGO_URL' in os.environ:
        settings['redis.sessions.url'] = os.environ['REDISTOGO_URL'] + '0'


def _setup_db(settings):
    # Allow overriding the model autocreation/deletion from the environment
    if 'MODEL_CREATE_ALL' in os.environ:
        settings['h.db.should_create_all'] = asbool(
            os.environ['MODEL_CREATE_ALL'])
    if 'MODEL_DROP_ALL' in os.environ:
        settings['h.db.should_drop_all'] = asbool(
            os.environ['MODEL_DROP_ALL'])
    if 'DEBUG_QUERY' in os.environ:
        level = logging.INFO
        if os.environ.get('DEBUG_QUERY') == 'trace':
            level = logging.DEBUG
        logging.getLogger('sqlalchemy.engine').setLevel(level)


def _setup_elasticsearch(settings):
    if 'ELASTICSEARCH_INDEX' in os.environ:
        settings['es.index'] = os.environ['ELASTICSEARCH_INDEX']

    if 'ELASTICSEARCH_HOST' in os.environ:
        settings['es.host'] = os.environ['ELASTICSEARCH_HOST']

    # ELASTICSEARCH_PORT and MAIL_PORT match Docker container links
    if 'ELASTICSEARCH_PORT' in os.environ:
        es_host = os.environ['ELASTICSEARCH_PORT_9200_TCP_ADDR']
        es_port = os.environ['ELASTICSEARCH_PORT_9200_TCP_PORT']
        settings['es.host'] = 'http://{}:{}'.format(es_host, es_port)


def _setup_email(settings):
    # MAILGUN_SMTP_LOGIN matches the Heroku environment variable
    if 'MAILGUN_SMTP_LOGIN' in os.environ:
        settings['mail.username'] = os.environ['MAILGUN_SMTP_LOGIN']
        settings['mail.password'] = os.environ['MAILGUN_SMTP_PASSWORD']
        settings['mail.host'] = 'smtp.mailgun.org'
        settings['mail.port'] = 587
        settings['mail.tls'] = True

    # MANDRILL_USERNAME matches the Heroku environment variable
    if 'MANDRILL_USERNAME' in os.environ:
        settings['mail.username'] = os.environ['MANDRILL_USERNAME']
        settings['mail.password'] = os.environ['MANDRILL_APIKEY']
        settings['mail.host'] = 'smtp.mandrillapp.com'
        settings['mail.port'] = 587
        settings['mail.tls'] = True

    # SENDGRID_USERNAME matches the Heroku environment variable
    if 'SENDGRID_USERNAME' in os.environ:
        settings['mail.username'] = os.environ['SENDGRID_USERNAME']
        settings['mail.password'] = os.environ['SENDGRID_PASSWORD']
        settings['mail.host'] = 'smtp.sendgrid.net'
        settings['mail.port'] = 587
        settings['mail.tls'] = True

    if 'MAIL_DEFAULT_SENDER' in os.environ:
        settings['mail.default_sender'] = os.environ['MAIL_DEFAULT_SENDER']

    if 'MAIL_PORT' in os.environ:
        mail_host = os.environ['MAIL_PORT_25_TCP_ADDR']
        mail_port = os.environ['MAIL_PORT_25_TCP_PORT']
        settings['mail.host'] = mail_host
        settings['mail.port'] = mail_port


def _setup_nsqd(settings):
    if 'NSQD_PORT' in os.environ:
        r_host = os.environ['NSQD_PORT_4150_TCP_ADDR']
        r_port = os.environ['NSQD_PORT_4150_TCP_PORT']
        settings['nsq.reader.addresses'] = '{}:{}'.format(r_host, r_port)
        w_host = os.environ['NSQD_PORT_4151_TCP_ADDR']
        w_port = os.environ['NSQD_PORT_4151_TCP_PORT']
        settings['nsq.writer.address'] = '{}:{}'.format(w_host, w_port)

    if 'NSQ_NAMESPACE' in os.environ:
        settings['nsq.namespace'] = os.environ['NSQ_NAMESPACE']


def _setup_redis(settings):
    if 'REDIS_PORT' in os.environ:
        redis_host = os.environ['REDIS_PORT_6379_TCP_ADDR']
        redis_port = os.environ['REDIS_PORT_6379_TCP_PORT']
        settings['redis.sessions.host'] = redis_host
        settings['redis.sessions.port'] = redis_port


def _setup_client(settings):
    if 'CLIENT_ID' in os.environ:
        settings['h.client_id'] = os.environ['CLIENT_ID']

    if 'CLIENT_SECRET' in os.environ:
        settings['h.client_secret'] = os.environ['CLIENT_SECRET']


def _setup_secrets(settings):
    if 'SECRET_KEY' in os.environ:
        settings['secret_key'] = os.environ['SECRET_KEY']
    elif 'SESSION_SECRET' in os.environ:
        log.warn('Found deprecated SESSION_SECRET environment variable. '
                 'Please use SECRET_KEY instead!')
        settings['secret_key'] = os.environ['SESSION_SECRET']


def _setup_statsd(settings):
    if 'STATSD_PORT' in os.environ:
        statsd_host = urlparse.urlparse(os.environ['STATSD_PORT_8125_UDP'])
        settings['statsd.host'] = statsd_host.hostname
        settings['statsd.port'] = statsd_host.port


def _setup_webassets(settings):
    if 'WEBASSETS_BASE_DIR' in os.environ:
        settings['webassets.base_dir'] = os.environ['WEBASSETS_BASE_DIR']
    if 'WEBASSETS_BASE_URL' in os.environ:
        settings['webassets.base_url'] = os.environ['WEBASSETS_BASE_URL']


def _setup_websocket(settings):
    if 'ALLOWED_ORIGINS' in os.environ:
        settings['origins'] = os.environ['ALLOWED_ORIGINS']

# -*- coding: utf-8 -*-
import logging
import os
import urlparse

from pyramid.config import Configurator
from pyramid.path import AssetResolver
from pyramid.response import FileResponse

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

log = logging.getLogger(__name__)


def includeme(config):
    config.include('pyramid_jinja2')
    config.include('pyramid_multiauth')
    config.include('h.api')
    config.include('h.models')
    config.include('h.streamer')
    config.include('h.subscribers')
    config.include('h.views')
    config.set_root_factory('h.resources.RootFactory')

    config.add_jinja2_renderer('.js')
    config.add_jinja2_renderer('.txt')
    config.add_jinja2_renderer('.html')

    favicon = AssetResolver().resolve('h:favicon.ico')
    config.add_route('favicon', '/favicon.ico')
    config.add_view(
        lambda request: FileResponse(favicon.abspath(), request=request),
        route_name='favicon'
    )

    config.add_route('ok', '/ruok')
    config.add_view(lambda request: 'imok', renderer='string', route_name='ok')


def create_app(settings):
    config = Configurator(settings=settings)
    config.include(includeme)
    return config.make_wsgi_app()


def main(global_config, **settings):
    overrides = _environment_overrides()

    settings.update(overrides)
    settings.update(global_config)

    return create_app(settings)


def _environment_overrides():
    overrides = {}

    # DATABASE_URL matches the Heroku environment variable
    if 'DATABASE_URL' in os.environ:
        _log_override('DATABASE_URL', 'sqlalchemy.url')
        urlparse.uses_netloc.append("postgres")
        urlparse.uses_netloc.append("sqlite")
        url = list(urlparse.urlparse(os.environ["DATABASE_URL"]))
        if url[0] == 'postgres':
            url[0] = 'postgresql+psycopg2'
        overrides['sqlalchemy.url'] = urlparse.urlunparse(url)

    if 'ELASTICSEARCH_INDEX' in os.environ:
        _log_override('ELASTICSEARCH_INDEX', 'es.index')
        overrides['es.index'] = os.environ['ELASTICSEARCH_INDEX']

    # ELASTICSEARCH_PORT and MAIL_PORT match Docker container links
    if 'ELASTICSEARCH_PORT' in os.environ:
        _log_override('ELASTICSEARCH_PORT', 'es.host')
        es_host = os.environ['ELASTICSEARCH_PORT_9200_TCP_ADDR']
        es_port = os.environ['ELASTICSEARCH_PORT_9200_TCP_PORT']
        overrides['es.host'] = 'http://{}:{}'.format(es_host, es_port)

    if 'MAIL_PORT' in os.environ:
        _log_override('MAIL_PORT', 'mail.host', 'mail.port')
        mail_host = os.environ['MAIL_PORT_25_TCP_ADDR']
        mail_port = os.environ['MAIL_PORT_25_TCP_PORT']
        overrides['mail.host'] = mail_host
        overrides['mail.port'] = mail_port

    if 'REDIS_PORT' in os.environ:
        _log_override('REDIS_PORT',
                      'redis.sessions.host', 'redis.sessions.port')
        redis_host = os.environ['REDIS_PORT_6379_TCP_ADDR']
        redis_port = os.environ['REDIS_PORT_6379_TCP_PORT']
        overrides['redis.sessions.host'] = redis_host
        overrides['redis.sessions.port'] = redis_port

    if 'SESSION_SECRET' in os.environ:
        _log_override('SESSION_SECRET',
                      'session.secret', 'redis.sessions.secret')
        overrides['session.secret'] = os.environ['SESSION_SECRET']
        overrides['redis.sessions.secret'] = os.environ['SESSION_SECRET']

    if 'STATSD_PORT' in os.environ:
        _log_override('STATSD_PORT', 'statsd.host', 'statsd.port')
        statsd_host = urlparse.urlparse(os.environ['STATSD_PORT_8125_UDP'])
        overrides['statsd.host'] = statsd_host.hostname
        overrides['statsd.port'] = statsd_host.port

    return overrides


def _log_override(env_var, *settings):
    log.debug("Found %s environment variable. Overriding setting of: %s",
              env_var, ", ".join(settings))

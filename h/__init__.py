# -*- coding: utf-8 -*-
import os
import urlparse
import uuid

from pyramid.config import Configurator
from pyramid.interfaces import ISessionFactory
from pyramid.path import AssetResolver
from pyramid.response import FileResponse
from pyramid.session import SignedCookieSessionFactory

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def includeme(config):
    config.set_root_factory('h.resources.RootFactory')

    config.include('pyramid_multiauth')

    config.include('h.api')
    config.include('h.models')
    config.include('h.streamer')
    config.include('h.subscribers')
    config.include('h.views')


def create_app(settings):
    config = Configurator(settings=settings)

    favicon = AssetResolver().resolve('h:favicon.ico')
    config.add_route('favicon', '/favicon.ico')
    config.add_view(
        lambda request: FileResponse(favicon.abspath(), request=request),
        route_name='favicon'
    )

    config.add_route('ok', '/ruok')
    config.add_view(lambda request: 'imok', renderer='string', route_name='ok')

    config.include(includeme)
    config.commit()

    # Register a default session factory if there is still none registered
    if config.registry.queryUtility(ISessionFactory) is None:
        random_secret = uuid.uuid4().hex + uuid.uuid4().hex
        session_factory = SignedCookieSessionFactory(random_secret)
        config.set_session_factory(session_factory)

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
        urlparse.uses_netloc.append("postgres")
        urlparse.uses_netloc.append("sqlite")
        url = list(urlparse.urlparse(os.environ["DATABASE_URL"]))
        if url[0] == 'postgres':
            url[0] = url[0] + '+psycopg2'
        overrides['sqlalchemy.url'] = urlparse.urlunparse(url)

    if 'ELASTICSEARCH_INDEX' in os.environ:
        overrides['es.index'] = os.environ['ELASTICSEARCH_INDEX']

    # ELASTICSEARCH_PORT_* and MAIL_PORT_* match Docker container links
    if 'ELASTICSEARCH_PORT' in os.environ:
        es_host = os.environ['ELASTICSEARCH_PORT_9200_TCP_ADDR']
        es_port = os.environ['ELASTICSEARCH_PORT_9200_TCP_PORT']
        overrides['es.host'] = 'http://{}:{}'.format(es_host, es_port)

    if 'MAIL_PORT' in os.environ:
        mail_host = os.environ['MAIL_PORT_25_TCP_ADDR']
        mail_port = os.environ['MAIL_PORT_25_TCP_PORT']
        overrides['mail.host'] = mail_host
        overrides['mail.port'] = mail_port

    return overrides

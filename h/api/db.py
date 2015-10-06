# -*- coding: utf-8 -*-

import logging
import time

from annotator import es
from elasticsearch import exceptions as elasticsearch_exceptions
from pyramid.settings import asbool
from sqlalchemy.ext import declarative


from .models import Annotation
from .models import Document


log = logging.getLogger(__name__)
Base = declarative.declarative_base()  # pylint: disable=invalid-name


def store_from_settings(settings):
    """Configure the Elasticsearch wrapper provided by annotator-store."""
    if 'es.host' in settings:
        es.host = settings['es.host']

    if 'es.index' in settings:
        es.index = settings['es.index']

    if 'es.compatibility' in settings:
        es.compatibility_mode = settings['es.compatibility']

    return es


def _ensure_es_plugins(es_conn):
    """Ensure that the ICU analysis plugin is installed for ES."""
    # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
    #
    # pylint: disable=unexpected-keyword-arg
    names = [x.strip() for x in es_conn.cat.plugins(h='component').split('\n')]
    if 'analysis-icu' not in names:
        message = ("ICU Analysis plugin is not installed for Elasticsearch\n"
                   "  See the installation instructions for more details:\n"
                   "  https://github.com/hypothesis/h/blob/master/"
                   "INSTALL.rst#installing")
        raise RuntimeError(message)


def create_db():
    """Create the Elasticsearch index for Annotations and Documents."""
    # Check for required plugin(s)
    _ensure_es_plugins(es.conn)

    models = [Annotation, Document]
    mappings = {}
    analysis = {}

    # Collect the mappings and analysis settings
    for model in models:
        mappings.update(model.get_mapping())
        for section, items in model.get_analysis().items():
            existing_items = analysis.setdefault(section, {})
            for name in items:
                if name in existing_items:
                    fmt = "Duplicate definition of 'index.analysis.{}.{}'."
                    msg = fmt.format(section, name)
                    raise RuntimeError(msg)
            existing_items.update(items)

    # Create the index
    try:
        # Pylint issue #258: https://bitbucket.org/logilab/pylint/issue/258
        #
        # pylint: disable=unexpected-keyword-arg
        response = es.conn.indices.create(es.index, ignore=400, body={
            'mappings': mappings,
            'settings': {'analysis': analysis},
        })
    except elasticsearch_exceptions.ConnectionError as e:
        msg = ('Can not access Elasticsearch at {0}! '
               'Check to ensure it is running.').format(es.host)
        raise elasticsearch_exceptions.ConnectionError('N/A', msg, e)

    # Bad request (400) is ignored above, to prevent warnings in the log, but
    # the failure could be for reasons other than that the index exists. If so,
    # raise the error here.
    if 'error' in response and 'IndexAlreadyExists' not in response['error']:
        raise elasticsearch_exceptions.RequestError(400, response['error'])

    # Update analysis settings
    settings = es.conn.indices.get_settings(index=es.index)
    existing = settings[es.index]['settings']['index'].get('analysis', {})
    if existing != analysis:
        try:
            es.conn.indices.close(index=es.index)
            es.conn.indices.put_settings(index=es.index, body={
                'analysis': analysis
            })
        finally:
            es.conn.indices.open(index=es.index)

    # Update mappings
    try:
        for doc_type, body in mappings.items():
            es.conn.indices.put_mapping(
                index=es.index,
                doc_type=doc_type,
                body=body
            )
    except elasticsearch_exceptions.RequestError as e:
        if e.error.startswith('MergeMappingException'):
            date = time.strftime('%Y-%m-%d')
            message = ("Elasticsearch index mapping is incorrect! Please "
                       "reindex it. For example, run: "
                       "./bin/hypothesis reindex {0} {1} {1}-{2}"
                       .format('yourconfig.ini', es.index, date)
                       )
            log.critical(message)
            raise RuntimeError(message)
        raise


def delete_db():
    """Delete the Annotation and Document databases."""
    Annotation.drop_all()
    Document.drop_all()


def use_session(session, base=Base):
    """Configure the SQLAlchemy base class to use the given session."""
    base.query = session.query_property()


def bind_engine(engine, base=Base, should_create=False, should_drop=False):
    """Bind the SQLAlchemy base class to the given engine."""
    base.metadata.bind = engine
    if should_drop:
        base.metadata.drop_all(engine)
    if should_create:
        base.metadata.create_all(engine)


def includeme(config):
    """Configure and possibly initialize Elasticsearch and its models."""
    registry = config.registry
    settings = registry.settings

    # Configure Elasticsearch
    es = store_from_settings(settings)

    # Add a property to all requests for easy access to the elasticsearch
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.add_request_method(lambda req: es, name='es', reify=True)

    # Maybe initialize the models
    if asbool(settings.get('h.db.should_drop_all', False)):
        delete_db()
    if asbool(settings.get('h.db.should_create_all', False)):
        create_db()

# -*- coding: utf-8 -*-
"""
A script to migrate annotation data from ElasticSearch to PostgreSQL.
"""
from __future__ import division, print_function, unicode_literals

import argparse
import datetime
import itertools
import os
import logging

from elasticsearch import helpers
from pyramid import paster
from pyramid.request import Request
from sqlalchemy.orm import scoped_session, sessionmaker

from h import db
from h.api.db import Base as APIBase
from h.api.models import elastic
from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentURI, DocumentMeta
from h.api.models.document import merge_documents

BATCH_SIZE = 2000

log = logging.getLogger('migrate')
logging.basicConfig(format='%(asctime)s %(process)d %(name)s [%(levelname)s] '
                           '%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.WARN)

parser = argparse.ArgumentParser('migrate')
parser.add_argument('config_uri',
                    help='paster configuration URI')

# We use our own session object to work around the fact that the default
# session is tied to the application's transaction manager, which makes using
# bulk_save_objects difficult.
Session = scoped_session(sessionmaker())


class Skip(Exception):

    """
    Raised in order to skip migration of an annotation.
    """

    pass


def main():
    args = parser.parse_args()

    request = Request.blank('/')
    env = paster.bootstrap(args.config_uri, request=request)
    request.root = env['root']

    engine = db.make_engine(request.registry.settings)
    Session.configure(bind=engine)

    APIBase.query = Session.query_property()

    if 'DEBUG_QUERY' in os.environ:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    migrate_annotations(request.legacy_es)
    print('')
    delete_nonexisting_annotations(request.legacy_es)


def migrate_annotations(es_client):
    annotations = scan(es_client, with_filter=scan_filter())
    started = False
    success = 0
    already = 0
    failure = 0

    print('{:d} annotations already imported'.format(Annotation.query.count()))

    start = datetime.datetime.now()
    for batch in _batch_iter(BATCH_SIZE, annotations):
        # Skip over annotations until we find the point from which we haven't
        # imported yet...
        if not started:
            skip, batch = find_start(batch)
            already += skip
            if not batch:
                continue
            started = True

        s, f = import_annotations(batch)

        success += s
        failure += f
        took = (datetime.datetime.now() - start).seconds
        print('{:d} ok, {:d} failed, took {:d} seconds'.format(
            success, failure, took))

        start = datetime.datetime.now()

    in_postgres = Annotation.query.count()
    in_elastic = es_client.conn.count(index=es_client.index,
                                      doc_type=es_client.t.annotation)['count']
    percent = 100 * (in_postgres / in_elastic)

    print('{:d} skipped as already-imported during this run'.format(already))
    print('{:d} imported this run'.format(success))
    print('{:d} failures this run'.format(failure))
    print('{:d} in postgres, {:d} in es = {:.2f}%'.format(in_postgres,
                                                          in_elastic,
                                                          percent))


def delete_nonexisting_annotations(es):
    print('Collecting Postgres annotation ids...')
    in_postgres = set((row.id for row in Session.query(Annotation.id)))
    print('Collected {:d} Postgres annotation ids'.format(len(in_postgres)))

    print('Collecting Elasticsearch annotation ids...')
    es_count = 0
    for batch in _batch_iter(BATCH_SIZE, scan(es)):
        in_postgres.difference_update((a['_id'] for a in batch))
        es_count += len(batch)

    print('Collected {:d} Elasticsearch annotation ids'.format(es_count))

    Session.query(Annotation).filter(Annotation.id.in_(in_postgres)).delete(synchronize_session=False)
    Session.commit()
    print('Deleted {:d} postgres annotations'.format(len(in_postgres)))


def scan(es_client, with_filter=None):
    query = {'query': {'match_all': {}}}

    if with_filter is not None:
        query['query'] = {
            'filtered': {
                'query': query['query'],
                'filter': with_filter,
            },
        }

    return helpers.scan(es_client.conn,
                        index=es_client.index,
                        doc_type=es_client.t.annotation,
                        query=query,
                        preserve_order=True,
                        scroll='1h',
                        sort='updated:asc')


def scan_filter():
    most_recent = Annotation.query.order_by(Annotation.updated.desc()).first()
    if most_recent:
        last_update = most_recent.updated.isoformat()
        return {'range': {'updated': {'gte': '{}||-1h/h'.format(last_update)}}}

    return None


def find_start(annotations):
    es_ids = [a['_id'] for a in annotations]
    db_annotations = Annotation.query.filter(Annotation.id.in_(es_ids))
    db_ids = set([a.id for a in db_annotations])

    skipped = len(db_ids)
    to_import = [a for a in annotations if a['_id'] not in db_ids]

    return skipped, to_import


def import_annotations(annotations):
    objs = set()

    failure = 0
    success = 0

    for a in annotations:
        try:
            data = a['_source']
            data['id'] = a['_id']
            es_annotation = elastic.Annotation(data)

            annotation = annotation_from_data(es_annotation)
            objs.add(annotation)

            create_or_update_document_objects(es_annotation)

            Session.flush()
        except Exception as e:
            log.warn('error importing %s: %s', a['_id'], e)
            failure += 1
        else:
            success += 1

    Session.bulk_save_objects(objs)
    Session.commit()

    return success, failure


def annotation_from_data(es_ann):
    # No joke. This is a thing.
    if es_ann.id == '_query':
        raise Skip("not an annotation (id=_query)")

    ann = Annotation.query.get(es_ann.id)
    if ann is None:
        ann = Annotation(id=es_ann.id)

    if es_ann.target_uri is None:
        raise Skip("annotation is missing a target source and uri")

    ann.created = es_ann.created
    ann.updated = es_ann.updated
    ann.userid = es_ann.userid
    ann.groupid = es_ann.groupid
    ann.text = es_ann.text
    ann.tags = es_ann.tags
    ann.references = es_ann.references
    ann.shared = es_ann.shared
    ann.target_uri = es_ann.target_uri
    ann.target_selectors = es_ann.target_selectors
    ann.extra = es_ann.extra

    return ann


def create_or_update_document_objects(es_ann):
    es_doc = es_ann.document

    if not es_doc:
        return

    uris = [u.uri for u in es_doc.document_uris]
    documents = Document.find_or_create_by_uris(Session, es_ann.target_uri, uris,
                                                created=es_doc.created,
                                                updated=es_doc.updated)

    if documents.count() > 1:
        document = merge_documents(Session, documents, updated=es_doc.updated)
    else:
        document = documents.first()

    document.updated = es_doc.updated

    for uri_ in es_doc.document_uris:
        create_or_update_document_uri(uri_, document)

    for meta in es_doc.meta:
        create_or_update_document_meta(meta, document)


def create_or_update_document_uri(es_docuri, pg_document):
    docuri = DocumentURI.query.filter(
            DocumentURI.claimant_normalized == es_docuri.claimant_normalized,
            DocumentURI.uri_normalized == es_docuri.uri_normalized,
            DocumentURI.type == es_docuri.type,
            DocumentURI.content_type == es_docuri.content_type).first()

    if docuri is None:
        docuri = DocumentURI(claimant=es_docuri.claimant,
                             uri=es_docuri.uri,
                             type=es_docuri.type,
                             content_type=es_docuri.content_type,
                             document=pg_document,
                             created=es_docuri.created,
                             updated=es_docuri.updated)
        Session.add(docuri)
    elif not docuri.document == pg_document:
        log.warn('Found DocumentURI with id %d does not match expected document with id %d', docuri.id, pg_document.id)

    docuri.updated = es_docuri.updated


def create_or_update_document_meta(es_meta, pg_document):
    meta = DocumentMeta.query.filter(
            DocumentMeta.claimant_normalized == es_meta.claimant_normalized,
            DocumentMeta.type == es_meta.normalized_type).one_or_none()

    if meta is None:
        meta = DocumentMeta(claimant=es_meta.claimant,
                            type=es_meta.normalized_type,
                            value=es_meta.value,
                            created=es_meta.created,
                            updated=es_meta.updated,
                            document=pg_document)
        Session.add(meta)
    else:
        meta.value = es_meta.value
        meta.updated = es_meta.updated
        if not meta.document == pg_document:
            log.warn('Found DocumentMeta with id %d does not match expected document with id %d', meta.id, pg_document.id)


def _batch_iter(n, iterable):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, n))
        if not batch:
            return
        yield batch


if __name__ == '__main__':
    main()

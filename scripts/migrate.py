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

    migrate_annotations(request.es)


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
            document_data = a['_source'].pop('document', None)
            data = a['_source']
            data['id'] = a['_id']
            es_annotation = elastic.Annotation(data)

            annotation = annotation_from_data(es_annotation)
            objs.add(annotation)

            if document_data is not None:
                document_objs_from_data(document_data, annotation)
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


def document_objs_from_data(data, ann):
    links = _transfom_document_links(ann.target_uri, data)
    uris = [link['uri'] for link in links]
    documents = Document.find_or_create_by_uris(Session, ann.target_uri, uris,
                                                created=ann.created,
                                                updated=ann.updated)

    if documents.count() > 1:
        document = merge_documents(Session, documents, updated=ann.updated)
    else:
        document = documents.first()

    document.updated = ann.updated

    document_uri_objs_from_data(document, links, ann)
    document_meta_objs_from_data(document, data, ann)


def document_uri_objs_from_data(document, transformed_links, ann):
    for link in transformed_links:
        docuri = DocumentURI.query.filter(
                DocumentURI.claimant_normalized == text_type(uri.normalize(link.get('claimant')), 'utf-8'),
                DocumentURI.uri_normalized == text_type(uri.normalize(link.get('uri')), 'utf-8'),
                DocumentURI.type == link.get('type'),
                DocumentURI.content_type == link.get('content_type')
                ).first()

        if docuri is None:
            docuri = DocumentURI(claimant=link.get('claimant'),
                                 uri=link.get('uri'),
                                 type=link.get('type'),
                                 content_type=link.get('content_type'),
                                 document=document,
                                 created=ann.created,
                                 updated=ann.updated)
            Session.add(docuri)
            Session.flush()

        docuri.updated = ann.updated


def document_meta_objs_from_data(document, data, ann, path_prefix=[]):
    _ = data.pop('link', None)

    for key, value in data.iteritems():
        keypath = path_prefix[:]
        keypath.append(key)

        if isinstance(value, dict):
            return document_meta_objs_from_data(document, value, ann,
                                                path_prefix=keypath)

        if not isinstance(value, list):
            value = [value]

        type = '.'.join(keypath)
        meta = DocumentMeta.query.filter(
                DocumentMeta.claimant_normalized == text_type(uri.normalize(ann.target_uri)),
                DocumentMeta.type == type).one_or_none()

        if meta is None:
            meta = DocumentMeta(claimant=ann.target_uri,
                                type='.'.join(keypath),
                                value=value,
                                created=ann.created,
                                updated=ann.updated,
                                document=document)
            Session.add(meta)
            Session.flush()
        else:
            meta.value = value
            meta.updated = ann.updated


def _batch_iter(n, iterable):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, n))
        if not batch:
            return
        yield batch


def _transfom_document_links(ann_target_uri, docdata):
    transformed = []
    doclinks = docdata.get('link', [])

    # When document link is just a string, transform it to a link object with
    # an href, so it gets further processed as either a self-claim or another
    # claim.
    if isinstance(doclinks, basestring):
        doclinks = [{"href": doclinks}]

    for link in doclinks:
        # disregard self-claim urls as they're are being added separately
        # later on.
        if link.keys() == ['href'] and link['href'] == ann_target_uri:
            continue

        # disregard doi links as these are being added separately from the
        # highwire and dc metadata later on.
        if link.keys() == ['href'] and link['href'].startswith('doi:'):
            continue

        uri_ = link['href']
        type = None

        # highwire pdf (href, type=application/pdf)
        if set(link.keys()) == set(['href', 'type']) and len(link.keys()) == 2:
            type = 'highwire-pdf'

        if type is None and link.get('rel') is not None:
            type = 'rel-{}'.format(link['rel'])

        content_type = None
        if link.get('type'):
            content_type = link['type']

        transformed.append({
            'claimant': ann_target_uri,
            'uri': uri_,
            'type': type,
            'content_type': content_type})

    # Add highwire doi link based on metadata
    hwdoivalues = docdata.get('highwire', {}).get('doi', [])
    for doi in hwdoivalues:
        if not doi.startswith('doi:'):
            doi = "doi:{}".format(doi)

        transformed.append({
            'claimant': ann_target_uri,
            'uri': doi,
            'type': 'highwire-doi'})

    # Add dc doi link based on metadata
    dcdoivalues = docdata.get('dc', {}).get('identifier', [])
    for doi in dcdoivalues:
        if not doi.startswith('doi:'):
            doi = "doi:{}".format(doi)

        transformed.append({
            'claimant': ann_target_uri,
            'uri': doi,
            'type': 'dc-doi'})

    # add self claim
    transformed.append({
        'claimant': ann_target_uri,
        'uri': ann_target_uri,
        'type': 'self-claim'})

    return transformed


if __name__ == '__main__':
    main()

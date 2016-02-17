# -*- coding: utf-8 -*-
"""
A script to migrate annotation data from ElasticSearch to PostgreSQL.
"""
from __future__ import division, print_function, unicode_literals

import argparse
import datetime
import dateutil.parser as dateparser
import itertools
import os
import logging

from elasticsearch import helpers
from pyramid import paster
from pyramid.request import Request
from sqlalchemy.orm import scoped_session, sessionmaker

from h import db
from h.api.db import Base as APIBase
from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentURI, DocumentMeta
from h.api.models.document import merge_documents
from h.api import uri
from h._compat import text_type

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
        print('{:d} ok, {:d} failed, took {:d} seconds'.format(success, failure, took))

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

            annotation = annotation_from_data(a['_id'], a['_source'])
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


def annotation_from_data(id, data):
    # No joke. This is a thing.
    if id == '_query':
        raise Skip("not an annotation (id=_query)")

    ann = Annotation(id=id)
    ann.created = dateparser.parse(data.pop('created')).replace(tzinfo=None)
    ann.updated = dateparser.parse(data.pop('updated')).replace(tzinfo=None)
    ann.userid = data.pop('user')
    ann.groupid = data.pop('group')

    text = data.pop('text', None)
    if text:
        ann.text = text

    tags = data.pop('tags', None)
    if tags:
        ann.tags = _filter_tags(tags)

    references = data.pop('references', None)
    if references:
        ann.references = _filter_references(references)

    perms = data.pop('permissions')
    ann.shared = _permissions_allow_sharing(ann.userid, ann.groupid, perms)

    targets = data.pop('target', [])
    target = targets[0] if len(targets) > 0 else None

    if target is not None:
        ann.target_uri = target.pop('source', None)
        ann.target_selectors = target.pop('selector', [])

    datauri = data.pop('uri', None)
    if ann.target_uri is None:
        ann.target_uri = datauri

    if ann.target_uri is None:
        raise Skip("annotation is missing a target source and uri")

    ann.target_uri_normalized = text_type(uri.normalize(ann.target_uri))

    if data:
        ann.extra = data

    return ann


def document_objs_from_data(data, ann):
    links = _transfom_document_links(ann.target_uri, data)
    uris = [link['uri'] for link in links]
    documents = Document.find_or_create_by_uris(ann.target_uri, uris,
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


def _filter_tags(tags):
    if isinstance(tags, basestring):
        return [tags]
    if not isinstance(tags, list):
        raise Skip("weird tags: {!r}".format(tags))
    return tags


def _filter_references(references):
    if not isinstance(references, list):
        raise Skip("non-list references field: {!r}".format(references))

    # Some of the values in the references fields aren't IDs (i.e. they're not
    # base64-encoded UUIDs or base64-encoded flake IDs. Instead, they're
    # base64-encoded random numbers between 0 and 1, in ASCII...
    #
    # So, we filter out things that couldn't possibly be valid IDs.
    references = [r for r in references if len(r) in [20, 22]]

    return references


def _permissions_allow_sharing(user, group, perms):
    gperm = 'group:{}'.format(group)

    allowed_keys = set(['admin', 'delete', 'read', 'update'])
    if set(perms) - allowed_keys:
        raise Skip("invalid permission keys: {!r}".format(perms))

    # Extract a (deduplicated) copy of the read perms field...
    read_perms = list(set(perms.get('read', [])))

    # We explicitly fix up some known weird scenarios with the permissions
    # field. The idea here is to cover the ones we've investigated and know
    # about, but throw a Skip if we see something we don't recognise. Then if
    # necessary we can make a decision on it and add a rule to handle it here.
    #
    # 1. Missing 'read' permissions field. Fix: set the permissions to private.
    if not read_perms:
        read_perms = [user]

    # 2. 'read' permissions field is [None]. Fix: as in 1).
    elif read_perms == [None]:
        read_perms = [user]

    # 3. Group 'read' permissions that don't match the annotation group. I
    #    believe this is a result of a bug where the focused group was
    #    incorrectly restored from localStorage.
    #
    #    CHECK THIS ONE: example annotation ids:
    #
    #    - AVHVDy7M8sFu_DXLVTfR (Jon)
    #    - AVH0xnzy8sFu_DXLVU8L (Jeremy)
    #    - AVHvR_bC8sFu_DXLVUl2 (Jeremy)
    #
    #    Fix: set the permissions to be the correct permissions for the group
    #    the annotation is actually in...
    elif (len(read_perms) == 1 and
          read_perms[0].startswith('group:') and
          read_perms != [gperm]):
        read_perms = [gperm]

    # 4. Read permissions includes 'group:__world__' but also other principals.
    #
    #    This is equivalent to including only 'group:__world__'.
    elif len(read_perms) > 1 and group == '__world__' and gperm in read_perms:
        read_perms = [gperm]

    if (read_perms != [gperm] and read_perms != [user]):
        # attempt to fix data when client auth state is out of sync by
        # by overriding the permissions with the user of the annotation.
        if read_perms[0].startswith('acct:'):
            read_perms = [user]
        else:
            raise Skip('invalid read permissions: {!r}'.format(perms))

    for other in ['admin', 'delete', 'update']:
        other_perms = perms.get(other, [])

        # If one of these is missing, who cares? We can assume it's supposed to
        # be the owner...
        if not other_perms:
            continue

        # Multiple permissions for one of these that includes the owner
        # accounts for about 20 annotations in the database. All of these fit
        # into one of the following categories:
        #
        # - created by staff for testing purposes
        # - modified post-hoc to allow admin editing of an annotation
        # - created by two non-staff users, for testing purposes (this accounts
        #   for a whole 3 annotations)
        if len(other_perms) > 1 and user in other_perms:
            continue

        if (other_perms != [user] and not other_perms[0].startswith('acct:')):
            raise Skip('invalid {} permissions: {!r}'.format(other, perms))

    # And, now, we ignore everything other than the read permissions. If
    # they're a group permission the annotation is considered "shared,"
    # otherwise not.
    if read_perms == [gperm]:
        return True

    return False


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

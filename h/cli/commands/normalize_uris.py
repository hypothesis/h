# -*- coding: utf-8 -*-

from h._compat import xrange
from collections import namedtuple

import click

from h import models
from h.models.document import merge_documents
from h.search import index
from h.util import uri


class Window(namedtuple("Window", ["start", "end"])):
    pass


@click.command("normalize-uris")
@click.pass_context
def normalize_uris(ctx):
    """
    Normalize all URIs in the database and reindex the changed annotations.
    """

    request = ctx.obj["bootstrap"]()

    normalize_document_uris(request)
    normalize_document_meta(request)
    normalize_annotations(request)


def normalize_document_uris(request):
    windows = _fetch_windows(request.db, models.DocumentURI.updated)
    request.tm.commit()

    for window in windows:
        request.tm.begin()
        _normalize_document_uris_window(request.db, window)
        request.tm.commit()


def normalize_document_meta(request):
    windows = _fetch_windows(request.db, models.DocumentMeta.updated)
    request.tm.commit()

    for window in windows:
        request.tm.begin()
        _normalize_document_meta_window(request.db, window)
        request.tm.commit()


def normalize_annotations(request):
    windows = _fetch_windows(request.db, models.Annotation.updated)
    request.tm.commit()

    for window in windows:
        request.tm.begin()
        ids = _normalize_annotations_window(request.db, window)
        request.tm.commit()

        request.tm.begin()
        _reindex_annotations(request, ids)
        request.tm.commit()


def _normalize_document_uris_window(session, window):
    query = (
        session.query(models.DocumentURI)
        .filter(models.DocumentURI.updated.between(window.start, window.end))
        .order_by(models.DocumentURI.updated.asc())
    )

    for docuri in query:
        documents = models.Document.find_by_uris(session, [docuri.uri])
        if documents.count() > 1:
            merge_documents(session, documents)

        existing = session.query(models.DocumentURI).filter(
            models.DocumentURI.id != docuri.id,
            models.DocumentURI.document_id == docuri.document_id,
            models.DocumentURI.claimant_normalized == uri.normalize(docuri.claimant),
            models.DocumentURI.uri_normalized == uri.normalize(docuri.uri),
            models.DocumentURI.type == docuri.type,
            models.DocumentURI.content_type == docuri.content_type,
        )

        if existing.count() > 0:
            session.delete(docuri)
        else:
            docuri._claimant_normalized = uri.normalize(docuri.claimant)
            docuri._uri_normalized = uri.normalize(docuri.uri)

        session.flush()


def _normalize_document_meta_window(session, window):
    query = (
        session.query(models.DocumentMeta)
        .filter(models.DocumentMeta.updated.between(window.start, window.end))
        .order_by(models.DocumentMeta.updated.asc())
    )

    for docmeta in query:
        existing = session.query(models.DocumentMeta).filter(
            models.DocumentMeta.id != docmeta.id,
            models.DocumentMeta.claimant_normalized == uri.normalize(docmeta.claimant),
            models.DocumentMeta.type == docmeta.type,
        )

        if existing.count() > 0:
            session.delete(docmeta)
        else:
            docmeta._claimant_normalized = uri.normalize(docmeta.claimant)

        session.flush()


def _normalize_annotations_window(session, window):
    query = (
        session.query(models.Annotation)
        .filter(models.Annotation.updated.between(window.start, window.end))
        .order_by(models.Annotation.updated.asc())
    )

    ids = set()
    for a in query:
        normalized = uri.normalize(a.target_uri)
        if normalized != a.target_uri_normalized:
            a._target_uri_normalized = normalized
            ids.add(a.id)

    return ids


def _reindex_annotations(request, ids):
    indexer = index.BatchIndexer(request.db, request.es, request)

    for _ in range(2):
        ids = indexer.index(ids)
        if not ids:
            break


def _fetch_windows(session, column, chunksize=100):
    updated = (
        session.query(column)
        .execution_options(stream_results=True)
        .order_by(column.desc())
        .all()
    )

    count = len(updated)
    windows = [
        Window(
            start=updated[min(x + chunksize, count) - 1].updated, end=updated[x].updated
        )
        for x in xrange(0, count, chunksize)
    ]

    return windows

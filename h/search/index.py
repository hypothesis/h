"""Functions for updating the search index."""

import logging
import time

import sqlalchemy as sa
from elasticsearch import helpers as es_helpers
from packaging.version import Version
from sqlalchemy.orm import subqueryload

from h import models, presenters

log = logging.getLogger(__name__)

PG_WINDOW_SIZE = 2500


class BatchIndexer:
    """A convenience class for reindexing annotations from the database to the search index."""

    def __init__(  # pylint: disable=too-many-arguments
        self, session, es_client, request, target_index=None, op_type="index"
    ):
        self.session = session
        self.es_client = es_client
        self.request = request
        self.op_type = op_type

        # By default, index into the open index
        if target_index is None:
            self._target_index = self.es_client.index
        else:
            self._target_index = target_index

    def index(self, annotation_ids: list, windowsize: int = PG_WINDOW_SIZE):
        """
        Reindex annotations.

        :param annotation_ids: a list of ids to reindex, reindexes all when `None`.
        :param windowsize: the number of annotations to index in between progress log statements

        :returns: a set of errored ids
        :rtype: set
        """
        annotations = _filtered_annotations(session=self.session, ids=annotation_ids)

        # Report indexing status as we go
        annotations = _log_status(annotations, log_every=windowsize)

        indexing = es_helpers.streaming_bulk(
            self.es_client.conn,
            annotations,
            chunk_size=2500,
            raise_on_error=False,
            expand_action_callback=self._prepare,
        )
        errored = set()
        for ok, item in indexing:
            if not ok:
                status = item[self.op_type]

                was_doc_exists_err = "document already exists" in status["error"]
                if self.op_type == "create" and was_doc_exists_err:
                    continue

                errored.add(status["_id"])
        return errored

    def _prepare(self, annotation):
        operation = {
            "_index": self._target_index,
            "_id": annotation.id,
        }
        if self.es_client.server_version < Version("7.0.0"):  # pragma: no cover
            operation["_type"] = self.es_client.mapping_type

        data = presenters.AnnotationSearchIndexPresenter(
            annotation, self.request
        ).asdict()

        return {self.op_type: operation}, data


def _filtered_annotations(session, ids):
    annotations = (
        _eager_loaded_annotations(session)
        .execution_options(stream_results=True)
        .filter(_annotation_filter())
        .filter(models.Annotation.id.in_(ids))
    )

    yield from annotations


def _annotation_filter():
    """Set the default filter for all search indexing operations."""
    return sa.not_(models.Annotation.deleted)


def _eager_loaded_annotations(session):
    return session.query(models.Annotation).options(
        subqueryload(models.Annotation.document).subqueryload(
            models.Document.document_uris
        ),
        subqueryload(models.Annotation.document).subqueryload(models.Document.meta),
        subqueryload(models.Annotation.moderation),
        subqueryload(models.Annotation.thread).load_only(models.Annotation.id),
    )


def _log_status(stream, log_every=1000):
    i = 0
    then = time.time()
    for item in stream:
        yield item
        i += 1
        if not i % log_every:
            now = time.time()
            delta = now - then
            then = now
            rate = round(log_every / delta)
            log.info("indexed %ik annotations, rate=%s/s", i // 1000, rate)

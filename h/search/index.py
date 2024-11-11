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

    def __init__(  # pylint: disable=too-many-arguments, too-many-positional-arguments
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

    def delete(self, annotation_ids: list[str]) -> None:
        """Delete `annotation_ids` from Elasticsearch."""

        # Delete the given annotations from Elasticsearch by sending them to
        # Elasticsearch's bulk API in chunks.
        #
        # Use streaming_bulk() rather than bulk() because of this comment in
        # the Elasticsearch docs:
        #
        # > When errors are being collected original document data is included
        # > in the error dictionary which can lead to an extra high memory
        # > usage. If you need to process a lot of data and want to
        # > ignore/collect errors please consider using the streaming_bulk()
        # > helper which will just return the errors and not store them in
        # > memory.
        # >
        # > https://elasticsearch-py.readthedocs.io/en/6.8.2/helpers.html#elasticsearch.helpers.bulk

        include_type = self._include_mapping_type()

        def delete_action(annotation_id):
            action = {
                "_index": self._target_index,
                "_id": annotation_id,
                "doc": {"deleted": True},
            }
            if include_type:  # pragma: no cover
                action["_type"] = self.es_client.mapping_type
            return action

        results = es_helpers.streaming_bulk(
            client=self.es_client.conn,
            actions=[delete_action(annotation_id) for annotation_id in annotation_ids],
            chunk_size=2500,
            raise_on_error=False,
        )

        for _ok, _item in results:
            # We aren't doing anything with the results yet
            # (but we still need this loop here to consume the `results`
            # generator, otherwise the requests don't actually get sent to
            # Elasticsearch).
            pass

    def _prepare(self, annotation):
        operation = {
            "_index": self._target_index,
            "_id": annotation.id,
        }
        if self._include_mapping_type():  # pragma: no cover
            operation["_type"] = self.es_client.mapping_type

        data = presenters.AnnotationSearchIndexPresenter(
            annotation, self.request
        ).asdict()

        return {self.op_type: operation}, data

    def _include_mapping_type(self):
        """Return True if the `_type` field should be included in request payloads."""
        return self.es_client.server_version < Version("7.0.0")


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

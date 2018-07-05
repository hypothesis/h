# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from collections import namedtuple
from contextlib import contextmanager

from elasticsearch1.exceptions import ConnectionTimeout

from h.search import query

log = logging.getLogger(__name__)

SearchResult = namedtuple('SearchResult', [
    'total',
    'annotation_ids',
    'reply_ids',
    'aggregations'])


class Search(object):
    """
    Search is the primary way to initiate a search on the annotation index.

    :param request: the request object
    :type request: pyramid.request.Request

    :param separate_replies: Wheter or not to return all replies to the
        annotations returned by this search. If this is True then the
        resulting annotations will only include top-level annotations, not replies.
    :type separate_replies: bool

    :param stats: An optional statsd client to which some metrics will be
        published.
    :type stats: statsd.client.StatsClient
    """
    def __init__(self, request, separate_replies=False, stats=None, _replies_limit=200):
        self.request = request
        self.es = request.es
        self.separate_replies = separate_replies
        self.stats = stats
        self._replies_limit = _replies_limit

        self.builder = self._default_querybuilder(request)
        self.reply_builder = self._default_querybuilder(request)

    def run(self, params):
        """
        Execute the search query

        :param params: the search parameters
        :type params: dict-like

        :returns: The search results
        :rtype: SearchResult
        """
        total, annotation_ids, aggregations = self._search_annotations(params)
        reply_ids = self._search_replies(annotation_ids)

        return SearchResult(total, annotation_ids, reply_ids, aggregations)

    def clear(self):
        """Clear search filters, aggregators, and matchers."""
        self.builder = query.Builder()
        self.reply_builder = query.Builder()

    def append_filter(self, filter_):
        """Append a search filter to the annotation and reply query."""
        self.builder.append_filter(filter_)
        self.reply_builder.append_filter(filter_)

    def append_matcher(self, matcher):
        """Append a search matcher to the annotation and reply query."""
        self.builder.append_matcher(matcher)
        self.reply_builder.append_matcher(matcher)

    def append_aggregation(self, aggregation):
        self.builder.append_aggregation(aggregation)

    def _search_annotations(self, params):
        if self.separate_replies:
            self.builder.append_filter(query.TopLevelAnnotationsFilter())

        response = None
        with self._instrument():
            response = self.es.conn.search(index=self.es.index,
                                           doc_type=self.es.mapping_type,
                                           _source=False,
                                           body=self.builder.build(params))
        total = response['hits']['total']
        annotation_ids = [hit['_id'] for hit in response['hits']['hits']]
        aggregations = self._parse_aggregation_results(response.get('aggregations', None))
        return (total, annotation_ids, aggregations)

    def _search_replies(self, annotation_ids):
        if not self.separate_replies:
            return []

        self.reply_builder.append_matcher(query.RepliesMatcher(annotation_ids))

        response = None
        with self._instrument():
            response = self.es.conn.search(
                index=self.es.index,
                doc_type=self.es.mapping_type,
                _source=False,
                body=self.reply_builder.build({'limit': self._replies_limit}))

        if len(response['hits']['hits']) < response['hits']['total']:
            log.warn("The number of reply annotations exceeded the page size "
                     "of the Elasticsearch query. We currently don't handle "
                     "this, our search API doesn't support pagination of the "
                     "reply set.")

        return [hit['_id'] for hit in response['hits']['hits']]

    def _parse_aggregation_results(self, aggregations):
        if not aggregations:
            return {}

        results = {}
        for key, result in aggregations.items():
            for agg in self.builder.aggregations:
                if key != agg.key:
                    continue

                results[key] = agg.parse_result(result)
                break

        return results

    @contextmanager
    def _instrument(self):
        if not self.stats:
            yield
            return

        s = self.stats.pipeline()
        timer = s.timer('search.query').start()
        try:
            yield
            s.incr('search.query.success')
        except ConnectionTimeout:
            s.incr('search.query.timeout')
            raise
        except:  # noqa: E722
            s.incr('search.query.error')
            raise
        finally:
            timer.stop()
            s.send()

    @staticmethod
    def _default_querybuilder(request):
        builder = query.Builder()
        builder.append_filter(query.DeletedFilter())
        builder.append_filter(query.AuthFilter(request))
        builder.append_filter(query.UriFilter(request))
        builder.append_filter(query.GroupFilter())
        builder.append_filter(query.GroupAuthFilter(request))
        builder.append_filter(query.UserFilter())
        builder.append_filter(query.NipsaFilter(request))
        builder.append_matcher(query.AnyMatcher())
        builder.append_matcher(query.TagsMatcher())
        return builder

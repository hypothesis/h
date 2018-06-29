# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
import newrelic.agent

from h import models, search
from h.util.view import json_view
from h.util.uri import normalize


def record_metrics(count,
                   request,
                   record_metric=newrelic.agent.record_custom_metric,
                   record_event=newrelic.agent.record_custom_event):
    if count > 0:
        record_event(
            'BadgeNotZero',
            {'user': "None" if request.user is None else request.user.username})
    else:
        record_metric('Custom/Badge/unAuthUserGotZero', int(request.user is None))
    record_metric('Custom/Badge/badgeCountIsZero', int(count == 0))


def _has_uri_ever_been_annotated(db, uri):
    """Return `True` if a given URI has ever been annotated."""

    # This check is written with SQL directly to guarantee an efficient query
    # and minimize SQLAlchemy overhead. We query `document_uri.uri_normalized`
    # instead of `annotation.target_uri_normalized` because there is an existing
    # index on `uri_normalized`.
    query = 'SELECT EXISTS(SELECT 1 FROM document_uri WHERE uri_normalized = :uri)'
    result = db.execute(query, {'uri': normalize(uri)}).first()
    return result[0] is True


@json_view(route_name='badge')
def badge(request):
    """Return the number of public annotations on a given page.

    This is for the number that's displayed on the Chrome extension's badge.

    Certain pages are blocklisted so that the badge never shows a number on
    those pages. The Chrome extension is oblivious to this, we just tell it
    that there are 0 annotations.

    """
    uri = request.params.get('uri')

    if not uri:
        raise httpexceptions.HTTPBadRequest()

    # Do a cheap check to see if this URI has ever been annotated. If not,
    # and most haven't, then we can skip the costs of a blocklist lookup or
    # search request. In addition to the Elasticsearch query, the search request
    # involves several DB queries to expand URIs and enumerate group IDs
    # readable by the current user.
    if not _has_uri_ever_been_annotated(request.db, uri):
        count = 0
    elif models.Blocklist.is_blocked(request.db, uri):
        count = 0
    else:
        query = {'uri': uri, 'limit': 0}
        result = search.Search(request, stats=request.stats).run(query)
        count = result.total

    record_metrics(count, request)

    return {'total': count}

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
import newrelic.agent

from h import models, search_old
from h.util.view import json_view


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

    if models.Blocklist.is_blocked(request.db, uri):
        count = 0
    else:
        query = {'uri': uri, 'limit': 0}
        result = search_old.Search(request, stats=request.stats).run(query)
        count = result.total

    record_metrics(count, request)

    return {'total': count}

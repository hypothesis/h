from pyramid import httpexceptions

from h import models
from h.util.view import json_view
from h.api import search as search_lib


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
        return {'total': 0}

    result = search_lib.search(request, {'uri': uri, 'limit': 0})

    return {'total': result.total}


def includeme(config):
    config.scan(__name__)
    config.add_route('badge', '/api/badge')

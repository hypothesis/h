from pyramid import httpexceptions

from h import models
from h.api.views import api_config
from h.api.resources import Root
from h.api import search as search_lib


@api_config(context=Root, name='blocklist')
def blocklist(request):
    """Return whether or not the given URI is blocklisted.

    And also the number of annotations of the URI (that the authorized user
    can read).

    """
    uri = request.params.get('uri')

    if not uri:
        raise httpexceptions.HTTPBadRequest()

    return {
        'total': search_lib.search(request, {'uri': uri, 'limit': 0})['total'],
        'blocked': models.Blocklist.is_blocked(uri)
    }


def includeme(config):
    config.scan(__name__)

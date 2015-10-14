from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.api import search as search_lib


@view_config(route_name='uriinfo',
             request_method='GET',
             accept='application/json',
             renderer='json',
             )
def uriinfo(request):
    """Return some info about the given URI.

    Currently returns:

      total:   the total number of annotations of this URI (that the authorized
               user can see)
      blocked: whether or not this URI is blocklisted

    """
    uri = request.params.get('uri')

    if not uri:
        raise httpexceptions.HTTPBadRequest()

    return {
        'total': search_lib.search(request, {'uri': uri, 'limit': 0})['total'],
        'blocked': models.Blocklist.is_blocked(uri)
    }


def includeme(config):
    config.add_route('uriinfo', '/app/uriinfo')
    config.scan(__name__)

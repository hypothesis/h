from json import dumps

from pyramid.view import view_config

from fanstatic import NEEDED
import js.annotator
import js.jquery

class Root(dict):
    __name__ = ''

@view_config(route_name='bookmarklet', renderer='bookmarklet/bookmarklet.jinja2')
def bookmarklet_view(request):
    annotator = request.environ[NEEDED].library_url(js.annotator.library)
    jquery = request.environ[NEEDED].library_url(js.jquery.library)

    root = Root()
    externals = {
        'source': request.resource_url(root, annotator,
                                       js.annotator.js.relpath),
        'styles': request.resource_url(root, annotator,
                                       js.annotator.css.relpath),
        'jQuery': request.resource_url(root, jquery,
                                       js.jquery.jquery.relpath)
    }

    config = {
        'externals': externals,
        'auth': {'tokenUrl': request.route_url('token')},
        'store': {'prefix': request.route_url('store', subpath='')[:-1]}
    }
    
    request.response.content_type = 'application/javascript'
    request.response.charset = 'utf-8'

    return {'config': dumps(config).replace('"', '\\"')}

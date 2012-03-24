from json import dumps

from pyramid.view import view_config

from fanstatic import NEEDED
import js.annotator
import js.jquery

@view_config(route_name='bookmarklet', renderer='bookmarklet/bookmarklet.jinja2')
def bookmarklet_view(request):
    annotator_base = request.environ[NEEDED].library_url(js.annotator.library)
    jquery_base = request.environ[NEEDED].library_url(js.jquery.library)

    externals = {
        'source': '/'.join([annotator_base, js.annotator.js.relpath]),
        'styles': '/'.join([annotator_base, js.annotator.css.relpath]),
        'jQuery': '/'.join([jquery_base, js.jquery.jquery.relpath])
    }

    config = {
        'externals': externals,
        'auth': {'tokenUrl': request.route_url('token')},
        'store': {'prefix': request.route_url('store', subpath='')[:-1]}
    }
    
    request.response.content_type = 'application/javascript'
    request.response.charset = 'utf-8'

    return {'config': dumps(config).replace('"', '\\"')}

from pyramid.view import view_config

from js.annotator import annotator

@view_config(route_name='bookmarklet.js',
             renderer='bookmarklet/bookmarklet.jinja2')
def bookmarklet_view(request):
    return {
        'root': request.application_url
    }

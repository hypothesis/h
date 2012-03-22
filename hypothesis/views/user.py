from pyramid.view import view_config

@view_config(route_name='bookmarklet', renderer='bookmarklet/bookmarklet.jinja2')
def bookmarklet_view(request):
    request.response.content_type = 'application/javascript'
    request.response.charset = 'utf-8'
    return {'root': request.application_url}

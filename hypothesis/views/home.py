from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

@view_config(route_name='home', renderer='home.jinja2')
def home_view(request):
    return {}

from apex import login, logout, register

from pyramid.security import authenticated_userid
from pyramid.view import view_config

@view_config(route_name='home', renderer='home.jinja2')
def home(request):
    if request.user is None: return login(request)
    return {}

def includeme(config):
    config.scan(__name__)
    config.include('pyramid_jinja2')
    config.add_jinja2_extension('jinja2.ext.do')
    config.add_jinja2_search_path('hypothesis:templates')
    config.add_jinja2_search_path('apex:templates')

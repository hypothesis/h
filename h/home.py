"""The home/front page of the //hypothes.is/ site."""
from pyramid import view

@view.view_config(route_name='index',
                  request_method='GET',
                  renderer='h:templates/home.html.jinja2')
def index(context, request):
    return {}


def includeme(config):
    config.add_route('index', '/')
    config.scan(__name__)

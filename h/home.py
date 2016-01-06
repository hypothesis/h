"""The home/front page of the //hypothes.is/ site."""
from pyramid import view
from pyramid import httpexceptions


@view.view_config(route_name='via_redirect',
                  request_method='GET')
def via_redirect(context, request):
    url = request.params.get('url')

    if url is None:
        raise httpexceptions.HTTPBadRequest('"url" parameter missing')


    via_link = 'https://via.hypothes.is/{}'.format(url)
    return httpexceptions.HTTPFound(location=via_link)


@view.view_config(route_name='index',
                  request_method='GET',
                  renderer='h:templates/old-home.html.jinja2')
def index(context, request):
    context = {}

    if request.authenticated_user:
        username = request.authenticated_user.username
        context['username'] = username
        context['user_profile_link'] = (
            request.route_url("stream") +
            "?q=user:{username}".format(username=username)
        )

    if request.feature('new_homepage'):
        request.override_renderer = 'h:templates/home.html.jinja2'

    return context


def includeme(config):
    config.add_route('index', '/')
    config.add_route('via_redirect', '/via')
    config.scan(__name__)

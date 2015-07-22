from pyramid import view
from pyramid import httpexceptions
from pyramid import i18n

from h.api import nipsa as nipsa_api
from h import util


_ = i18n.TranslationStringFactory(__package__)


@view.view_config(route_name='nipsa_index', request_method='GET',
                  renderer='h:templates/nipsa.html.jinja2',
                  permission='admin')
def index(_):
    return {"userids": [util.split_user(u)[0] for u in nipsa_api.index()]}


@view.view_config(route_name='nipsa_index', request_method='POST',
                  renderer='h:templates/nipsa.html.jinja2',
                  permission='admin')
def add_nipsa(request):
    username = request.params["add"]

    # It's important that we nipsa the full user ID
    # ("acct:seanh@hypothes.is" not just "seanh").
    userid = util.userid_from_username(username, request)

    nipsa_api.add_nipsa(request, userid)
    return index(request)


@view.view_config(route_name='remove_nipsa', request_method='POST',
                  renderer='h:templates/nipsa.html.jinja2',
                  permission='admin')
def remove_nipsa(request):
    username = request.params["remove"]
    userid = util.userid_from_username(username, request)
    nipsa_api.remove_nipsa(request, userid)
    return httpexceptions.HTTPSeeOther(
        location=request.route_url("nipsa_index"))


def includeme(config):
    config.add_route('nipsa_index', '/nipsa')
    config.add_route('remove_nipsa', '/remove_nipsa')
    config.scan(__name__)

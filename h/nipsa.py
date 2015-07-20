from pyramid import view
from pyramid import httpexceptions
from pyramid import i18n

from h.api import nipsa as nipsa_api
from h import util


_ = i18n.TranslationStringFactory(__package__)


@view.view_config(route_name='nipsa_index', request_method='GET',
                  renderer='h:templates/nipsa.html',
                  permission='admin')
def index(_):
    return {"userids": [util.split_user(u)[0] for u in nipsa_api.index()]}


@view.view_config(route_name='nipsa_index', request_method='POST',
                  renderer='h:templates/nipsa.html',
                  permission='admin')
def nipsa(request):
    username = request.params["add"]

    # It's important that we nipsa the full user ID
    # ("acct:seanh@hypothes.is" not just "seanh").
    userid = util.userid_from_username(username, request)

    nipsa_api.nipsa(request, userid)
    return index(request)


@view.view_config(route_name='unnipsa', request_method='POST',
                  renderer='h:templates/nipsa.html',
                  permission='admin')
def unnipsa(request):
    username = request.params["remove"]
    userid = util.userid_from_username(username, request)
    nipsa_api.unnipsa(request, userid)
    return httpexceptions.HTTPSeeOther(
        location=request.route_url("nipsa_index"))


def includeme(config):
    config.add_route('nipsa_index', '/nipsa')
    config.add_route('unnipsa', '/unnipsa')
    config.scan(__name__)

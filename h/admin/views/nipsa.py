# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import nipsa
from h import util


@view_config(route_name='admin_nipsa',
             request_method='GET',
             renderer='h:templates/admin/nipsa.html.jinja2',
             permission='admin_nipsa')
def nipsa_index(_):
    return {"usernames": [util.user.split_user(u)["username"]
                          for u in nipsa.index()]}


@view_config(route_name='admin_nipsa',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/nipsa.html.jinja2',
             permission='admin_nipsa')
def nipsa_add(request):
    username = request.params["add"]

    # It's important that we nipsa the full user ID
    # ("acct:seanh@hypothes.is" not just "seanh").
    userid = util.user.userid_from_username(username, request)

    nipsa.add_nipsa(request, userid)
    return nipsa_index(request)


@view_config(route_name='admin_nipsa',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/nipsa.html.jinja2',
             permission='admin_nipsa')
def nipsa_remove(request):
    username = request.params["remove"]
    userid = util.user.userid_from_username(username, request)
    nipsa.remove_nipsa(request, userid)
    return httpexceptions.HTTPSeeOther(
        location=request.route_url("admin_nipsa"))


def includeme(config):
    config.scan(__name__)

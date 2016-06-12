# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import util
from h.i18n import TranslationString as _


@view_config(route_name='admin_nipsa',
             request_method='GET',
             renderer='h:templates/admin/nipsa.html.jinja2',
             permission='admin_nipsa')
def nipsa_index(request):
    nipsa_service = request.find_service(name='nipsa')
    return {"usernames": [util.user.split_user(u)["username"]
                          for u in nipsa_service.flagged_userids]}


@view_config(route_name='admin_nipsa',
             request_method='POST',
             request_param='add',
             permission='admin_nipsa')
def nipsa_add(request):
    username = request.params["add"]

    if username:
        userid = util.user.userid_from_username(username, request)
        nipsa_service = request.find_service(name='nipsa')
        nipsa_service.flag(userid)
    else:
        request.session.flash(_('Please supply a username!'), 'error')

    index = request.route_path("admin_nipsa")
    return httpexceptions.HTTPSeeOther(index)


@view_config(route_name='admin_nipsa',
             request_method='POST',
             request_param='remove',
             permission='admin_nipsa')
def nipsa_remove(request):
    username = request.params["remove"]

    if username:
        userid = util.user.userid_from_username(username, request)
        nipsa_service = request.find_service(name='nipsa')
        nipsa_service.unflag(userid)
    else:
        request.session.flash(_('Please supply a username!'), 'error')

    index = request.route_path("admin_nipsa")
    return httpexceptions.HTTPSeeOther(index)


def includeme(config):
    config.scan(__name__)

# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h import util
from h.i18n import TranslationString as _


class UserNotFoundError(Exception):
    pass


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
    user = _form_request_user(request, 'add')

    nipsa_service = request.find_service(name='nipsa')
    nipsa_service.flag(user.userid)

    index = request.route_path("admin_nipsa")
    return httpexceptions.HTTPSeeOther(index)


@view_config(route_name='admin_nipsa',
             request_method='POST',
             request_param='remove',
             permission='admin_nipsa')
def nipsa_remove(request):
    user = _form_request_user(request, 'remove')

    nipsa_service = request.find_service(name='nipsa')
    nipsa_service.unflag(user.userid)

    index = request.route_path("admin_nipsa")
    return httpexceptions.HTTPSeeOther(index)


@view_config(context=UserNotFoundError)
def user_not_found(exc, request):
    request.session.flash(exc.message, 'error')
    return httpexceptions.HTTPFound(location=request.route_path('admin_nipsa'))


def _form_request_user(request, param):
    username = request.params[param]
    user = models.User.get_by_username(request.db, username)

    if user is None:
        raise UserNotFoundError(
            _("Could not find user with username %s" % username)
        )

    return user


def includeme(config):
    config.scan(__name__)

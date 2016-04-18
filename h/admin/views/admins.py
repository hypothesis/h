# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import accounts
from h import models
from h.i18n import TranslationString as _


@view_config(route_name='admin_admins',
             request_method='GET',
             renderer='h:templates/admin/admins.html.jinja2',
             permission='admin_admins')
def admins_index(_):
    """A list of all the admin users as an HTML page."""
    return {"admin_users": [u.username for u in models.User.admins()]}


@view_config(route_name='admin_admins',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/admins.html.jinja2',
             permission='admin_admins')
def admins_add(request):
    """Make a given user an admin."""
    username = request.params['add']
    try:
        accounts.make_admin(username)
    except accounts.NoSuchUserError:
        request.session.flash(
            _("User {username} doesn't exist.".format(username=username)),
            "error")
    return admins_index(request)


@view_config(route_name='admin_admins',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/admins.html.jinja2',
             permission='admin_admins')
def admins_remove(request):
    """Remove a user from the admins."""
    if len(models.User.admins()) > 1:
        username = request.params['remove']
        user = models.User.get_by_username(username)
        user.admin = False
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_admins'))


def includeme(config):
    config.scan(__name__)

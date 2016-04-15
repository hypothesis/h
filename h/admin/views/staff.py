# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import accounts
from h import models
from h.i18n import TranslationString as _


@view_config(route_name='admin_staff',
             request_method='GET',
             renderer='h:templates/admin/staff.html.jinja2',
             permission='admin_staff')
def staff_index(_):
    """A list of all the staff members as an HTML page."""
    return {"staff": [u.username for u in models.User.staff_members()]}


@view_config(route_name='admin_staff',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/staff.html.jinja2',
             permission='admin_staff')
def staff_add(request):
    """Make a given user a staff member."""
    username = request.params['add']
    try:
        accounts.make_staff(username)
    except accounts.NoSuchUserError:
        request.session.flash(
            _("User {username} doesn't exist.".format(username=username)),
            "error")
    return staff_index(request)


@view_config(route_name='admin_staff',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/staff.html.jinja2',
             permission='admin_staff')
def staff_remove(request):
    """Remove a user from the staff."""
    username = request.params['remove']
    user = models.User.get_by_username(username)
    user.staff = False
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_staff'))


def includeme(config):
    config.scan(__name__)

# -*- coding: utf-8 -*-
from pyramid import session
from pyramid import view
from pyramid import httpexceptions

from h.api import nipsa
from h.i18n import TranslationString as _
from h import accounts
from h import models
from h import util


@view.view_config(route_name='admin_index',
                  request_method='GET',
                  renderer='h:templates/admin/index.html.jinja2',
                  permission='admin')
def index(_):
    return {}


@view.view_config(route_name='admin_features',
                  request_method='GET',
                  renderer='h:templates/admin/features.html.jinja2',
                  permission='admin')
def features_index(_):
    return {"features": models.Feature.all()}


@view.view_config(route_name='admin_features',
                  request_method='POST',
                  permission='admin')
def features_save(request):
    session.check_csrf_token(request)
    for feat in models.Feature.all():
        for attr in ['everyone', 'admins', 'staff']:
            val = request.POST.get('{0}[{1}]'.format(feat.name, attr))
            if val == 'on':
                setattr(feat, attr, True)
            else:
                setattr(feat, attr, False)
    request.session.flash(_("Changes saved."), "success")
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_features'))


@view.view_config(route_name='admin_nipsa',
                  request_method='GET',
                  renderer='h:templates/admin/nipsa.html.jinja2',
                  permission='admin')
def nipsa_index(_):
    return {"userids": [util.split_user(u)[0] for u in nipsa.index()]}


@view.view_config(route_name='admin_nipsa',
                  request_method='POST',
                  renderer='h:templates/admin/nipsa.html.jinja2',
                  permission='admin')
def nipsa_add(request):
    username = request.params["add"]

    # It's important that we nipsa the full user ID
    # ("acct:seanh@hypothes.is" not just "seanh").
    userid = util.userid_from_username(username, request)

    nipsa.add_nipsa(request, userid)
    return nipsa_index(request)


@view.view_config(route_name='admin_nipsa_remove',
                  request_method='POST',
                  renderer='h:templates/admin/nipsa.html.jinja2',
                  permission='admin')
def nipsa_remove(request):
    username = request.params["remove"]
    userid = util.userid_from_username(username, request)
    nipsa.remove_nipsa(request, userid)
    return httpexceptions.HTTPSeeOther(
        location=request.route_url("admin_nipsa"))


@view.view_config(route_name='admin_admins',
                  request_method='GET',
                  renderer='h:templates/admin/admins.html.jinja2',
                  permission='admin')
def admins_index(_):
    """A list of all the admin users as an HTML page."""
    return {"admin_users": [u.username for u in models.User.admins()]}


@view.view_config(route_name='admin_admins',
                  request_method='POST',
                  renderer='h:templates/admin/admins.html.jinja2',
                  permission='admin')
def admins_add(request):
    """Make a given user an admin."""
    try:
        username = request.params['add']
    except KeyError:
        raise httpexceptions.HTTPNotFound()

    try:
        accounts.make_admin(username)
    except accounts.NoSuchUserError:
        request.session.flash(
            _("User {username} doesn't exist.".format(username=username)),
            "error")
    return admins_index(request)


@view.view_config(route_name='admin_admins_remove',
                  request_method='POST',
                  renderer='h:templates/admin/admins.html.jinja2',
                  permission='admin')
def admins_remove(request):
    """Remove a user from the admins."""
    if len(models.User.admins()) > 1:
        try:
            username = request.params['remove']
        except KeyError:
            raise httpexceptions.HTTPNotFound()

        user = models.User.get_by_username(username)
        user.admin = False
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_admins'))


@view.view_config(route_name='admin_staff',
                  request_method='GET',
                  renderer='h:templates/admin/staff.html.jinja2',
                  permission='admin')
def staff_index(_):
    """A list of all the staff members as an HTML page."""
    return {"staff": [u.username for u in models.User.staff_members()]}


@view.view_config(route_name='admin_staff',
                  request_method='POST',
                  renderer='h:templates/admin/staff.html.jinja2',
                  permission='admin')
def staff_add(request):
    """Make a given user a staff member."""
    try:
        username = request.params['add']
    except KeyError:
        raise httpexceptions.HTTPNotFound()

    try:
        accounts.make_staff(username)
    except accounts.NoSuchUserError:
        request.session.flash(
            _("User {username} doesn't exist.".format(username=username)),
            "error")
    return staff_index(request)


@view.view_config(route_name='admin_staff_remove',
                  request_method='POST',
                  renderer='h:templates/admin/staff.html.jinja2',
                  permission='admin')
def staff_remove(request):
    """Remove a user from the staff."""
    try:
        username = request.params['remove']
    except KeyError:
        raise httpexceptions.HTTPNotFound()

    user = models.User.get_by_username(username)
    user.staff = False
    return httpexceptions.HTTPSeeOther(
        location=request.route_url('admin_staff'))


@view.view_config(route_name='admin_users',
                  request_method='GET',
                  renderer='h:templates/admin/users.html.jinja2',
                  permission='admin')
def users_index(request):
    user = None
    username = request.params.get('username')

    if username is not None:
        user = models.User.get_by_username(username)

    return {'username': username, 'user': user}


@view.view_config(route_name='admin_badge',
                  request_method='GET',
                  renderer='h:templates/admin/badge.html.jinja2',
                  permission='admin')
def badge_index(_):
    return {"uris": models.BadgeBlocklist.all()}


@view.view_config(route_name='admin_badge',
                  request_method='POST',
                  request_param='add',
                  renderer='h:templates/admin/badge.html.jinja2',
                  permission='admin')
def badge_add(request):
    try:
        request.db.add(models.BadgeBlocklist(uri=request.params['add']))
    except ValueError as err:
        request.session.flash(err.message, 'error')
    return badge_index(request)


@view.view_config(route_name='admin_badge',
                  request_method='POST',
                  request_param='remove',
                  renderer='h:templates/admin/badge.html.jinja2',
                  permission='admin')
def badge_remove(request):
    uri = request.params['remove']
    request.db.delete(models.BadgeBlocklist.get_by_uri(uri))
    return badge_index(request)


def includeme(config):
    config.add_route('admin_index', '/admin')
    config.add_route('admin_features', '/admin/features')
    config.add_route('admin_nipsa', '/admin/nipsa')
    config.add_route('admin_nipsa_remove', '/admin/nipsa/remove')
    config.add_route('admin_admins', '/admin/admins')
    config.add_route('admin_admins_remove', '/admin/admins/remove')
    config.add_route('admin_staff', '/admin/staff')
    config.add_route('admin_staff_remove', '/admin/staff/remove')
    config.add_route('admin_users', '/admin/users')
    config.add_route('admin_badge', '/admin/badge')
    config.scan(__name__)

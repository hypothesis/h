# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.i18n import TranslationString as _  # noqa: N813


@view_config(route_name='admin_admins',
             request_method='GET',
             renderer='h:templates/admin/admins.html.jinja2',
             permission='admin_admins')
def admins_index(request):
    """A list of all the admin users as an HTML page."""
    admins = request.db.query(models.User).filter(models.User.admin)
    return {
        "admin_users": [u.userid for u in admins],
        "default_authority": request.authority,
    }


@view_config(route_name='admin_admins',
             request_method='POST',
             request_param='add',
             renderer='h:templates/admin/admins.html.jinja2',
             permission='admin_admins',
             require_csrf=True)
def admins_add(request):
    """Make a given user an admin."""
    username = request.params['add'].strip()
    authority = request.params['authority'].strip()
    user = models.User.get_by_username(request.db, username, authority)
    if user is None:
        request.session.flash(
            _("User {username} doesn't exist.".format(username=username)),
            "error")
    else:
        user.admin = True
    index = request.route_path('admin_admins')
    return httpexceptions.HTTPSeeOther(location=index)


@view_config(route_name='admin_admins',
             request_method='POST',
             request_param='remove',
             renderer='h:templates/admin/admins.html.jinja2',
             permission='admin_admins',
             require_csrf=True)
def admins_remove(request):
    """Remove a user from the admins."""
    n_admins = request.db.query(models.User).filter(models.User.admin).count()
    if n_admins > 1:
        userid = request.params['remove']
        user = request.db.query(models.User).filter_by(userid=userid).first()
        if user is not None:
            user.admin = False
    index = request.route_path('admin_admins')
    return httpexceptions.HTTPSeeOther(location=index)

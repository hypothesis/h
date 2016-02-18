# -*- coding: utf-8 -*-
from pyramid import session
from pyramid import view
from pyramid import httpexceptions

from elasticsearch import helpers as es_helpers

from h.api import nipsa
from h.api import storage
from h.i18n import TranslationString as _
from h import accounts
from h import models
from h import paginator
from h import util


class UserDeletionError(Exception):
    pass


@view.view_config(route_name='admin_index',
                  request_method='GET',
                  renderer='h:templates/admin/index.html.jinja2',
                  permission='admin_index')
def index(_):
    return {}


@view.view_config(route_name='admin_features',
                  request_method='GET',
                  renderer='h:templates/admin/features.html.jinja2',
                  permission='admin_features')
def features_index(_):
    return {"features": models.Feature.all()}


@view.view_config(route_name='admin_features',
                  request_method='POST',
                  permission='admin_features')
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
                  permission='admin_nipsa')
def nipsa_index(_):
    return {"usernames": [util.user.split_user(u)["username"]
                          for u in nipsa.index()]}


@view.view_config(route_name='admin_nipsa',
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


@view.view_config(route_name='admin_nipsa',
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


@view.view_config(route_name='admin_admins',
                  request_method='GET',
                  renderer='h:templates/admin/admins.html.jinja2',
                  permission='admin_admins')
def admins_index(_):
    """A list of all the admin users as an HTML page."""
    return {"admin_users": [u.username for u in models.User.admins()]}


@view.view_config(route_name='admin_admins',
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


@view.view_config(route_name='admin_admins',
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


@view.view_config(route_name='admin_staff',
                  request_method='GET',
                  renderer='h:templates/admin/staff.html.jinja2',
                  permission='admin_staff')
def staff_index(_):
    """A list of all the staff members as an HTML page."""
    return {"staff": [u.username for u in models.User.staff_members()]}


@view.view_config(route_name='admin_staff',
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


@view.view_config(route_name='admin_staff',
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


@view.view_config(route_name='admin_users',
                  request_method='GET',
                  renderer='h:templates/admin/users.html.jinja2',
                  permission='admin_users')
def users_index(request):
    user = None
    user_meta = {}
    username = request.params.get('username')

    if username:
        user = models.User.get_by_username(username)
        if user is None:
            user = models.User.get_by_email(username)

    if user is not None:
        # Fetch information on how many annotations the user has created
        query = _all_user_annotations_query(request, user)
        result = request.es.conn.count(index=request.es.index,
                                       doc_type=request.es.t.annotation,
                                       body={'query': query})
        user_meta['annotations_count'] = result['count']

    return {'username': username, 'user': user, 'user_meta': user_meta}


@view.view_config(route_name='admin_users_delete',
                  request_method='POST',
                  permission='admin_users')
def users_delete(request):
    username = request.params.get('username')
    user = models.User.get_by_username(username)

    if user is None:
        request.session.flash(
            'Cannot find user with username %s' % username, 'error')
    else:
        try:
            delete_user(request, user)
            request.session.flash(
                'Successfully deleted user %s' % username, 'success')
        except UserDeletionError as e:
            request.session.flash(str(e), 'error')

    return httpexceptions.HTTPFound(
        location=request.route_path('admin_users'))


@view.view_config(route_name='admin_badge',
                  request_method='GET',
                  renderer='h:templates/admin/badge.html.jinja2',
                  permission='admin_badge')
def badge_index(_):
    return {"uris": models.Blocklist.all()}


@view.view_config(route_name='admin_badge',
                  request_method='POST',
                  request_param='add',
                  renderer='h:templates/admin/badge.html.jinja2',
                  permission='admin_badge')
def badge_add(request):
    try:
        request.db.add(models.Blocklist(uri=request.params['add']))
    except ValueError as err:
        request.session.flash(err.message, 'error')
    return badge_index(request)


@view.view_config(route_name='admin_badge',
                  request_method='POST',
                  request_param='remove',
                  renderer='h:templates/admin/badge.html.jinja2',
                  permission='admin_badge')
def badge_remove(request):
    uri = request.params['remove']
    request.db.delete(models.Blocklist.get_by_uri(uri))
    return badge_index(request)


@view.view_config(route_name='admin_groups',
                  request_method='GET',
                  renderer='h:templates/admin/groups.html.jinja2',
                  permission='admin_groups')
@paginator.paginate
def groups_index(context, request):
    return models.Group.query.order_by(models.Group.created.desc())


@view.view_config(route_name='admin_groups_csv',
                  request_method='GET',
                  renderer='csv',
                  permission='admin_groups')
def groups_index_csv(request):
    groups = models.Group.query

    header = ['Group name', 'Group URL', 'Creator username',
              'Creator email', 'Number of members']
    rows = [[group.name,
             request.route_url('group_read',
                               pubid=group.pubid,
                               slug=group.slug),
             group.creator.username,
             group.creator.email,
             len(group.members)] for group in groups]

    filename = 'groups.csv'
    request.response.content_disposition = 'attachment;filename=' + filename

    return {'header': header, 'rows': rows}


def delete_user(request, user):
    """
    Deletes a user with all their group memberships and annotations.

    Raises UserDeletionError when deletion fails with the appropriate error
    message.
    """

    if models.Group.created_by(user).count() > 0:
        raise UserDeletionError('Cannot delete user who is a group creator.')

    user.groups = []

    query = _all_user_annotations_query(request, user)
    annotations = es_helpers.scan(client=request.es.conn, query={'query': query})
    for annotation in annotations:
        storage.delete_annotation(annotation['_id'])

    request.db.delete(user)


def _all_user_annotations_query(request, user):
    """Query matching all annotations (shared and private) owned by user."""
    userid = util.user.userid_from_username(user.username, request)
    return {
        'filtered': {
            'filter': {'term': {'user': userid.lower()}},
            'query': {'match_all': {}}
        }
    }


def includeme(config):
    config.add_route('admin_index', '/')
    config.add_route('admin_features', '/features')
    config.add_route('admin_nipsa', '/nipsa')
    config.add_route('admin_admins', '/admins')
    config.add_route('admin_staff', '/staff')
    config.add_route('admin_users', '/users')
    config.add_route('admin_users_delete', '/users/delete')
    config.add_route('admin_groups', '/groups')
    config.add_route('admin_groups_csv', '/groups.csv')
    config.add_route('admin_badge', '/badge')
    config.scan(__name__)

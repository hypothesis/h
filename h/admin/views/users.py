# -*- coding: utf-8 -*-

from elasticsearch import helpers as es_helpers
import jinja2
from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.accounts.events import ActivationEvent
from h.admin import worker
from h.admin.services.user import UserRenameError
from memex import storage
from h.i18n import TranslationString as _


class UserDeletionError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


@view_config(route_name='admin_users',
             request_method='GET',
             renderer='h:templates/admin/users.html.jinja2',
             permission='admin_users')
def users_index(request):
    user = None
    user_meta = {}
    username = request.params.get('username')

    if username:
        username = username.strip()
        user = models.User.get_by_username(request.db, username)
        if user is None:
            user = models.User.get_by_email(request.db, username, request.auth_domain)

    if user is not None:
        n_annots = _all_user_annotations(request, user).count()
        user_meta['annotations_count'] = n_annots

    return {'username': username, 'user': user, 'user_meta': user_meta}


@view_config(route_name='admin_users_activate',
             request_method='POST',
             request_param='username',
             permission='admin_users')
def users_activate(request):
    user = _form_request_user(request)

    user.activate()

    request.session.flash(jinja2.Markup(_(
        'User {name} has been activated!'.format(name=user.username))),
        'success')

    request.registry.notify(ActivationEvent(request, user))

    return httpexceptions.HTTPFound(
        location=request.route_path('admin_users',
                                    _query=(('username', user.username),)))


@view_config(route_name='admin_users_rename',
             request_method='POST',
             permission='admin_users')
def users_rename(request):
    user = _form_request_user(request)

    old_username = user.username
    new_username = request.params.get('new_username').strip()

    try:
        svc = request.find_service(name='rename_user')
        svc.check(new_username)

        worker.rename_user.delay(user.id, new_username)

        request.session.flash(
            'The user "%s" will be renamed to "%s" in the backgroud. Refresh this page to see if it\'s already done' %
            (old_username, new_username), 'success')

        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users',
                                        _query=(('username', new_username),)))

    except (UserRenameError, ValueError) as e:
        request.session.flash(str(e), 'error')
        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users',
                                        _query=(('username', old_username),)))


@view_config(route_name='admin_users_delete',
             request_method='POST',
             permission='admin_users')
def users_delete(request):
    user = _form_request_user(request)

    try:
        delete_user(request, user)
        request.session.flash(
            'Successfully deleted user %s' % user.username, 'success')
    except UserDeletionError as e:
        request.session.flash(str(e), 'error')

    return httpexceptions.HTTPFound(
        location=request.route_path('admin_users'))


@view_config(context=UserNotFoundError)
def user_not_found(exc, request):
    request.session.flash(jinja2.Markup(_(exc.message)), 'error')
    return httpexceptions.HTTPFound(location=request.route_path('admin_users'))


def delete_user(request, user):
    """
    Deletes a user with all their group memberships and annotations.

    Raises UserDeletionError when deletion fails with the appropriate error
    message.
    """

    if models.Group.created_by(request.db, user).count() > 0:
        raise UserDeletionError('Cannot delete user who is a group creator.')

    user.groups = []

    query = _all_user_annotations_query(request, user)
    annotations = es_helpers.scan(client=request.es.conn, query={'query': query})
    for annotation in annotations:
        storage.delete_annotation(request.db, annotation['_id'])

    request.db.delete(user)


def _all_user_annotations_query(request, user):
    """Query matching all annotations (shared and private) owned by user."""
    return {
        'filtered': {
            'filter': {'term': {'user': user.userid.lower()}},
            'query': {'match_all': {}}
        }
    }


def _all_user_annotations(request, user):
    return (request.db.query(models.Annotation)
            .filter(models.Annotation.userid == user.userid)
            .yield_per(100))


def _form_request_user(request):
    """Return the User which a user admin form action relates to."""
    username = request.params['username'].strip()
    user = models.User.get_by_username(request.db, username)

    if user is None:
        raise UserNotFoundError("Could not find user with username %s" % username)

    return user


def includeme(config):
    config.scan(__name__)

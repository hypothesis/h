# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import jinja2
from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h import storage
from h.accounts.events import ActivationEvent
from h.events import AnnotationEvent
from h.services.rename_user import UserRenameError
from h.tasks.admin import rename_user
from h.i18n import TranslationString as _  # noqa


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
    authority = request.params.get('authority')

    if username:
        username = username.strip()
        authority = authority.strip()
        user = models.User.get_by_username(request.db, username, authority)
        if user is None:
            user = models.User.get_by_email(request.db, username, authority)

    if user is not None:
        svc = request.find_service(name='annotation_stats')
        counts = svc.user_annotation_counts(user.userid)
        user_meta['annotations_count'] = counts['total']

    return {
        'default_authority': request.authority,
        'username': username,
        'authority': authority,
        'user': user,
        'user_meta': user_meta
    }


@view_config(route_name='admin_users_activate',
             request_method='POST',
             request_param='userid',
             permission='admin_users',
             require_csrf=True)
def users_activate(request):
    user = _form_request_user(request)

    user.activate()

    request.session.flash(jinja2.Markup(_(
        'User {name} has been activated!'.format(name=user.username))),
        'success')

    request.registry.notify(ActivationEvent(request, user))

    return httpexceptions.HTTPFound(
        location=request.route_path('admin_users',
                                    _query=(('username', user.username),
                                            ('authority', user.authority))))


@view_config(route_name='admin_users_rename',
             request_method='POST',
             permission='admin_users',
             require_csrf=True)
def users_rename(request):
    user = _form_request_user(request)

    old_username = user.username
    new_username = request.params.get('new_username').strip()

    try:
        svc = request.find_service(name='rename_user')
        svc.check(user, new_username)

        rename_user.delay(user.id, new_username)

        request.session.flash(
            'The user "%s" will be renamed to "%s" in the backgroud. Refresh this page to see if it\'s already done' %
            (old_username, new_username), 'success')

        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users',
                                        _query=(('username', new_username),
                                                ('authority', user.authority))))

    except (UserRenameError, ValueError) as e:
        request.session.flash(str(e), 'error')
        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users',
                                        _query=(('username', old_username),
                                                ('authority', user.authority))))


@view_config(route_name='admin_users_delete',
             request_method='POST',
             permission='admin_users',
             require_csrf=True)
def users_delete(request):
    user = _form_request_user(request)

    try:
        delete_user(request, user)
        request.session.flash(
            'Successfully deleted user %s with authority %s' % (user.username, user.authority), 'success')
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
    annotations = request.db.query(models.Annotation) \
                            .filter_by(userid=user.userid)
    for annotation in annotations:
        storage.delete_annotation(request.db, annotation.id)
        event = AnnotationEvent(request, annotation.id, 'delete')
        request.notify_after_commit(event)

    request.db.delete(user)


def _form_request_user(request):
    """Return the User which a user admin form action relates to."""
    userid = request.params['userid'].strip()
    user_service = request.find_service(name='user')
    user = user_service.fetch(userid)

    if user is None:
        raise UserNotFoundError("Could not find user with userid %s" % userid)

    return user

# -*- coding: utf-8 -*-

from elasticsearch import helpers as es_helpers
import jinja2
from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h import util
from h.accounts.events import ActivationEvent
from h.api import storage
from h.api.search.index import BatchIndexer
from h.i18n import TranslationString as _
from h.util.user import userid_from_username


class UserDeletionError(Exception):
    pass


class UserRenameError(Exception):
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
        user = models.User.get_by_username(request.db, username)
        if user is None:
            user = models.User.get_by_email(request.db, username)

    if user is not None:
        # Fetch information on how many annotations the user has created
        query = _all_user_annotations_query(request, user)
        result = request.es.conn.count(index=request.es.index,
                                       doc_type=request.es.t.annotation,
                                       body={'query': query})
        user_meta['annotations_count'] = result['count']

    return {'username': username, 'user': user, 'user_meta': user_meta}


@view_config(route_name='admin_users_activate',
             request_method='POST',
             request_param='username',
             permission='admin_users')
def users_activate(request):
    user = _form_request_user(request)

    if user is None:
        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users'))

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

    if user is None:
        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users'))

    old_username = user.username
    new_username = request.params.get('new_username')

    try:
        rename_user(request, user, new_username)

        request.session.flash(
            'Successfully renamed user "%s" to "%s"' %
            (old_username, new_username), 'success')

        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users',
                                        _query=(('username', new_username),)))

    except (UserRenameError, ValueError) as e:
        request.session.flash(str(e), 'error')
        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users',
                                        _query=(('username', old_username),)))


def rename_user(request, user, new_username):
    """
    Change the username of `user` to `new_username`.

    Validates the new username and updates the User. The permissions of
    the user's annotations are updated to reflect the new username.

    May raise a ValueError if the new username does not validate or
    UserRenameError if the new username is already taken by another account.
    """
    existing_user = models.User.get_by_username(request.db, new_username)

    if existing_user:
        raise UserRenameError('Another user already has the username "%s"' % new_username)

    old_userid = userid_from_username(user.username, request)
    new_userid = userid_from_username(new_username, request)

    user.username = new_username

    annotations = request.db.query(models.Annotation).filter(
        models.Annotation.userid == old_userid).yield_per(100)
    ids = set()
    for annotation in annotations:
        annotation.userid = new_userid
        ids.add(annotation.id)

    request.tm.commit()

    indexer = BatchIndexer(request.db, request.es, request)
    indexer.index(ids)


@view_config(route_name='admin_users_delete',
             request_method='POST',
             permission='admin_users')
def users_delete(request):
    user = _form_request_user(request)

    if user is None:
        return httpexceptions.HTTPFound(
            location=request.route_path('admin_users'))

    try:
        delete_user(request, user)
        request.session.flash(
            'Successfully deleted user %s' % user.username, 'success')
    except UserDeletionError as e:
        request.session.flash(str(e), 'error')

    return httpexceptions.HTTPFound(
        location=request.route_path('admin_users'))


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
    userid = util.user.userid_from_username(user.username, request.auth_domain)
    return {
        'filtered': {
            'filter': {'term': {'user': userid.lower()}},
            'query': {'match_all': {}}
        }
    }


def _form_request_user(request):
    """Return the User which a user admin form action relates to."""
    username = request.params['username']
    user = models.User.get_by_username(request.db, username)

    if user is None:
        request.session.flash(jinja2.Markup(_(
            "User {name} doesn't exist!".format(name=username))),
            'error')

    return user


def includeme(config):
    config.scan(__name__)

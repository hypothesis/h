# -*- coding: utf-8 -*-

from elasticsearch import helpers as es_helpers
import jinja2
from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h import util
from h.accounts.events import ActivationEvent
from h.api import storage
from h.i18n import TranslationString as _


class UserDeletionError(Exception):
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
    username = request.params['username']
    user = models.User.get_by_username(request.db, username)

    if user is None:
        request.session.flash(jinja2.Markup(_(
            "User {name} doesn't exist!".format(name=username))),
            'error')
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


@view_config(route_name='admin_users_delete',
             request_method='POST',
             permission='admin_users')
def users_delete(request):
    username = request.params.get('username')
    user = models.User.get_by_username(request.db, username)

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


def includeme(config):
    config.scan(__name__)

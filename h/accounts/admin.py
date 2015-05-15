# -*- coding: utf-8 -*-
import re
from pkg_resources import resource_stream

from pyramid.view import view_config
from pyramid import httpexceptions
from hem.db import get_session

from .models import User

ADMIN_LIST = None


def get_admins():
    global ADMIN_LIST
    if ADMIN_LIST is None:
        ADMIN_LIST = set(
            l.strip().lower()
            for l in resource_stream(__package__, '../../conf/admins')
        )
    return ADMIN_LIST


def get_username(userid, domain):
    match = re.match(r'acct:([^@]+)@{}'.format(domain), userid)
    if match:
        return match.group(1)
    else:
        return None


def _verify_admin(request):
    if not request.unauthenticated_userid:
        raise httpexceptions.HTTPNotFound()
    user = get_username(request.unauthenticated_userid, request.domain)

    if user not in get_admins():
        # User is not an admin
        raise httpexceptions.HTTPNotFound()


@view_config(route_name='nipsa_list',
             renderer='json')
def nipsa_list(request):
    _verify_admin(request)

    users = User.get_nipsa_users(request)
    return {'users': users}


@view_config(route_name='admin_user',
             request_method='POST',
             accept='application/json',
             renderer='json')
def update_settings(request):
    _verify_admin(request)

    # Check whether all users exist
    # Bail out at the first non-existing user
    for username in request.json_body.keys():
        user = User.get_by_username(request, username)
        if not user:
            return {
                'status': 'failure',
                'errors': 'Invalid request',
                'reason': 'User does not exist:' + username
            }

    # Only proceed if all users exist
    for username in request.json_body.keys():
        settings = request.json_body[username]
        if 'nipsa' in settings:
            user = User.get_by_username(request, username)
            user.nipsa = settings['nipsa']
            db = get_session(request)
            db.add(user)
    return {'status': 'okay'}


def includeme(config):
    config.add_route('nipsa_list', '/admin/nipsa.list')
    config.add_route('admin_user', '/admin/settings')
    config.scan(__name__)

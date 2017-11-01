# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest

from h.views.api import api_config
from h.views.api_config import cors_policy


@api_config(route_name='api.group_member',
            request_method='DELETE',
            link_name='group.member.delete',
            description='Remove the current user from a group.',
            effective_principals=security.Authenticated)
def remove_member(group, request):
    """Remove a member from the given group."""

    # Currently, we only support removing the requesting user
    if request.matchdict.get('user') == 'me':
        userid = request.authenticated_userid
    else:
        raise HTTPBadRequest('Only the "me" user value is currently supported')

    group_service = request.find_service(name='group')
    group_service.member_leave(group, userid)

    return HTTPNoContent()


@api_config(route_name='api.group_read',
            request_method='GET',
            description='Read a Group',
            renderer='json')
def get_group(group, request):
    return dict((f, getattr(group, f, None)) for f in ('pubid', 'description', 'name'))


@api_config(route_name='api.group_read_noslug',
            link_name='group.read',
            request_method='GET',
            decorator=cors_policy)
def read_noslug(group, request):
    redirect_to_with_slug(group, request)


def redirect_to_with_slug(group, request):
    """Redirect if the request slug does not match that of the group."""
    slug = request.matchdict.get('slug')
    if slug is None or slug != group.slug:
        path = request.route_path(
            'api.group_read', pubid=group.pubid, slug=group.slug)
        raise httpexceptions.HTTPMovedPermanently(path)

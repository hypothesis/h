# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest
from h.presenters import GroupsJSONPresenter
from h.views.api import api_config


@api_config(route_name='api.groups',
            request_method='GET',
            link_name='groups.read',
            description="Fetch the user's groups")
def groups(request):
    authority = request.params.get('authority')
    document_uri = request.params.get('document_uri')
    svc = request.find_service(name='list_groups')
    all_groups = svc.all_groups(user=request.user,
                                authority=authority,
                                document_uri=document_uri)
    all_groups = GroupsJSONPresenter(all_groups, request.route_url).asdicts()
    return all_groups


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

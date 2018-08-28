# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest, HTTPNotFound

from h.auth.util import request_auth_client, validate_auth_client_authority
from h.presenters import GroupJSONPresenter, GroupsJSONPresenter
from h.schemas.api.group import CreateGroupAPISchema, GetGroupsAPISchema
from h.traversal import GroupContext
from h.views.api.config import api_config


@api_config(route_name='api.groups',
            request_method='GET',
            link_name='groups.read',
            description="Fetch the user's groups",
            query_schema=GetGroupsAPISchema())
def groups(request):
    authority = request.validated_params['authority']
    document_uri = request.validated_params['document_uri']
    expand = request.validated_params['expand']

    list_svc = request.find_service(name='list_groups')

    if request.user is not None:
        authority = request.user.authority
    else:
        authority = authority or request.authority
    all_groups = list_svc.request_groups(user=request.user,
                                         authority=authority,
                                         document_uri=document_uri)
    all_groups = [GroupContext(group, request) for group in all_groups]
    all_groups = GroupsJSONPresenter(all_groups).asdicts(expand=expand)
    return all_groups


@api_config(route_name='api.groups',
            request_method='POST',
            effective_principals=security.Authenticated,
            description='Create a new group',
            body_schema=CreateGroupAPISchema())
def create(request):
    """Create a group from the POST payload."""

    appstruct = request.validated_body
    group_properties = {
        'name': appstruct['name'],
        'description': appstruct.get('description', None),
    }

    group_service = request.find_service(name='group')

    group = group_service.create_private_group(
        group_properties['name'],
        request.user.userid,
        description=group_properties['description'],
    )

    group_context = GroupContext(group, request)
    return GroupJSONPresenter(group_context).asdict(expand=['organization'])


@api_config(route_name='api.group_member',
            request_method='DELETE',
            link_name='group.member.delete',
            description='Remove the current user from a group.',
            effective_principals=security.Authenticated)
def remove_member(group, request):
    """Remove a member from the given group."""

    # Currently, we only support removing the requesting user
    if request.matchdict.get('userid') == 'me':
        userid = request.authenticated_userid
    else:
        raise HTTPBadRequest('Only the "me" user value is currently supported')

    group_service = request.find_service(name='group')
    group_service.member_leave(group, userid)

    return HTTPNoContent()


@api_config(route_name='api.group_member',
            request_method='POST',
            link_name='group.member.add',
            description='Add the user in the request params to a group.')
def add_member(group, request):
    """Add a member to a given group.

    :raises HTTPNotFound: if the user is not found or if the use and group
      authorities don't match.
    """
    client = request_auth_client(request)

    user_svc = request.find_service(name='user')
    group_svc = request.find_service(name='group')

    user = user_svc.fetch(request.matchdict['userid'])

    if user is None:
        raise HTTPNotFound()

    validate_auth_client_authority(client, user.authority)

    if user.authority != group.authority:
        raise HTTPNotFound()

    group_svc.member_join(group, user.userid)

    return HTTPNoContent()

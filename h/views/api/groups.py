# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import security
from pyramid.httpexceptions import HTTPNoContent, HTTPBadRequest, HTTPNotFound

from h.auth.util import request_auth_client, validate_auth_client_authority
from h.exceptions import PayloadError
from h.presenters import GroupJSONPresenter, GroupsJSONPresenter
from h.schemas.api.group import CreateGroupAPISchema
from h.schemas import ValidationError
from h.traversal import GroupContext
from h.views.api.config import api_config


@api_config(route_name='api.groups',
            request_method='GET',
            link_name='groups.read',
            description="Fetch the user's groups")
def groups(request):
    authority = request.params.get('authority')
    document_uri = request.params.get('document_uri')
    expand = request.GET.getall('expand') or []

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
            description='Create a new group')
def create(request):
    """Create a group from the POST payload."""
    if request.user is None:
        raise ValidationError('Request must have an authenticated user')

    schema = CreateGroupAPISchema()

    appstruct = schema.validate(_json_payload(request))
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

    try:
        user = user_svc.fetch(request.matchdict['userid'])
    except ValueError:
        raise HTTPNotFound()

    if user is None:
        raise HTTPNotFound()

    validate_auth_client_authority(client, user.authority)

    if user.authority != group.authority:
        raise HTTPNotFound()

    group_svc.member_join(group, user.userid)

    return HTTPNoContent()


# @TODO This is a duplication of code in h.views.api — move to a util module
def _json_payload(request):
    """
    Return a parsed JSON payload for the request.

    :raises PayloadError: if the body has no valid JSON body
    """
    try:
        return request.json_body
    except ValueError:
        raise PayloadError()

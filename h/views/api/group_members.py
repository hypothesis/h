import logging

from pyramid.config import not_
from pyramid.httpexceptions import HTTPConflict, HTTPNoContent, HTTPNotFound

from h.presenters import GroupMembershipJSONPresenter
from h.schemas.api.group_membership import EditGroupMembershipAPISchema
from h.schemas.pagination import Pagination
from h.security import Permission
from h.services.group_members import ConflictError
from h.traversal import (
    AddGroupMembershipContext,
    EditGroupMembershipContext,
    GroupContext,
    GroupMembershipContext,
)
from h.views.api.config import api_config
from h.views.api.helpers.json_payload import json_payload

log = logging.getLogger(__name__)


LIST_MEMBERS_API_CONFIG = {
    "versions": ["v1", "v2"],
    "route_name": "api.group_members",
    "request_method": "GET",
    "link_name": "group.members.read",
    "description": "Fetch a list of all members of a group",
    "permission": Permission.Group.READ,
}


@api_config(request_param=not_("page[number]"), **LIST_MEMBERS_API_CONFIG)
def list_members_legacy(context: GroupContext, request):
    """Legacy version of the list-members API, maintained for backwards-compatibility."""
    assert context.group is not None, "Group is required"  # noqa: S101

    log.info(
        "list_members_legacy() was called. User-Agent: %s, Referer: %s, pubid: %s",
        request.headers.get("User-Agent"),
        request.headers.get("Referer"),
        context.group.pubid,
    )

    # Get the list of memberships from GroupMembersService instead of just
    # accessing `context.memberships` because GroupMembersService returns the
    # memberships explictly sorted by creation date then username whereas
    # `context.memberships` is unsorted.
    group_members_service = request.find_service(name="group_members")
    memberships = group_members_service.get_memberships(context.group)

    return [
        GroupMembershipJSONPresenter(request, membership).asdict()
        for membership in memberships
    ]


@api_config(request_param="page[number]", **LIST_MEMBERS_API_CONFIG)
def list_members(context: GroupContext, request):
    group = context.group
    group_members_service = request.find_service(name="group_members")

    pagination = Pagination.from_params(request.params)

    total = group_members_service.count_memberships(group)
    memberships = group_members_service.get_memberships(
        group, offset=pagination.offset, limit=pagination.limit
    )

    membership_dicts = [
        GroupMembershipJSONPresenter(request, membership).asdict()
        for membership in memberships
    ]

    return {"meta": {"page": {"total": total}}, "data": membership_dicts}


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="GET",
    link_name="group.member.read",
    description="Fetch a group membership",
    permission=Permission.Group.READ,
)
def get_member(context: GroupMembershipContext, request):
    return GroupMembershipJSONPresenter(request, context.membership).asdict()


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="DELETE",
    link_name="group.member.delete",
    description="Remove a user from a group",
    permission=Permission.Group.MEMBER_REMOVE,
)
def remove_member(context: GroupMembershipContext, request):
    group_members_service = request.find_service(name="group_members")

    group_members_service.member_leave(context.group, context.user.userid)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="POST",
    link_name="group.member.add",
    description="Add a user to a group",
    permission=Permission.Group.MEMBER_ADD,
)
def add_member(context: AddGroupMembershipContext, request):
    if context.user.authority != context.group.authority:
        raise HTTPNotFound()  # noqa: RSE102

    if request.body:
        appstruct = EditGroupMembershipAPISchema().validate(json_payload(request))
        roles = appstruct["roles"]
    else:
        # This doesn't mean the membership will be created with no roles:
        # default roles will be applied by the service.
        roles = None

    group_members_service = request.find_service(name="group_members")

    try:
        membership = group_members_service.member_join(
            context.group, context.user.userid, roles
        )
    except ConflictError as err:
        raise HTTPConflict(str(err)) from err

    return GroupMembershipJSONPresenter(request, membership).asdict()


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="PATCH",
    link_name="group.member.edit",
    description="Change a user's role in a group",
)
def edit_member(context: EditGroupMembershipContext, request):
    appstruct = EditGroupMembershipAPISchema().validate(json_payload(request))
    context.new_roles = appstruct["roles"]

    if not request.has_permission(Permission.Group.MEMBER_EDIT, context):
        raise HTTPNotFound()  # noqa: RSE102

    if context.membership.roles != context.new_roles:
        old_roles = context.membership.roles
        context.membership.roles = context.new_roles  # type: ignore[assignment]
        log.info(
            "Changed group membership roles: %r (previous roles were: %r)",
            context.membership,
            old_roles,
        )

    if context.user == request.user:
        # Update request.identity.user.memberships so permissions checks done
        # by GroupMembershipJSONPresenter below return the right results.
        # Otherwise permissions checks will be based on the old roles.
        for membership in request.identity.user.memberships:
            if membership.group.id == context.group.id:
                membership.roles = context.new_roles

    return GroupMembershipJSONPresenter(request, context.membership).asdict()

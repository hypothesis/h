import logging

from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

from h.presenters import GroupMembershipJSONPresenter
from h.schemas.api.group_membership import EditGroupMembershipAPISchema
from h.security import Permission
from h.traversal import EditGroupMembershipContext, GroupContext, GroupMembershipContext
from h.views.api.config import api_config
from h.views.api.helpers.json_payload import json_payload

log = logging.getLogger(__name__)


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_members",
    request_method="GET",
    link_name="group.members.read",
    description="Fetch a list of all members of a group",
    permission=Permission.Group.READ,
)
def list_members(context: GroupContext, request):
    return [
        GroupMembershipJSONPresenter(request, membership).asdict()
        for membership in context.group.memberships
    ]


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
def add_member(context: GroupMembershipContext, request):
    group_members_service = request.find_service(name="group_members")

    if context.user.authority != context.group.authority:
        raise HTTPNotFound()

    group_members_service.member_join(context.group, context.user.userid)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="PATCH",
    link_name="group.member.edit",
    description="Change a user's role in a group",
)
def edit_member(context: GroupMembershipContext, request):
    appstruct = EditGroupMembershipAPISchema().validate(json_payload(request))
    new_roles = appstruct["roles"]

    if not request.has_permission(
        Permission.Group.MEMBER_EDIT,
        EditGroupMembershipContext(
            context.group, context.user, context.membership, new_roles
        ),
    ):
        raise HTTPNotFound()

    if context.membership.roles != new_roles:
        old_roles = context.membership.roles
        context.membership.roles = new_roles
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
                membership.roles = new_roles

    return GroupMembershipJSONPresenter(request, context.membership).asdict()

from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound

from h.presenters import UserJSONPresenter
from h.security import Permission
from h.traversal import GroupContext, GroupMembershipContext
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_members",
    request_method="GET",
    link_name="group.members.read",
    description="Fetch all members of a group",
    permission=Permission.Group.READ,
)
def read_members(context: GroupContext, _request):
    """Fetch the members of a group."""
    return [UserJSONPresenter(user).asdict() for user in context.group.members]


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="DELETE",
    link_name="group.member.delete",
    description="Remove the current user from a group",
    is_authenticated=True,
    permission=Permission.Group.MEMBER_REMOVE,
)
def remove_member(context: GroupMembershipContext, request):
    """Remove a member from the given group."""

    group_members_service = request.find_service(name="group_members")
    group_members_service.member_leave(context.group, context.user.userid)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="POST",
    link_name="group.member.add",
    permission=Permission.Group.MEMBER_ADD,
    description="Add the user in the request params to a group.",
)
def add_member(context: GroupMembershipContext, request):
    """
    Add a member to a given group.

    :raise HTTPNotFound: if the user is not found or if the use and group
      authorities don't match.
    """
    group_members_svc = request.find_service(name="group_members")

    if context.user.authority != context.group.authority:
        raise HTTPNotFound()

    group_members_svc.member_join(context.group, context.user.userid)

    return HTTPNoContent()

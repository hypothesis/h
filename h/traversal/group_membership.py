from dataclasses import dataclass

from pyramid.httpexceptions import HTTPNotFound

from h.exceptions import InvalidUserId
from h.models import Group, GroupMembership, GroupMembershipRoles, User


@dataclass
class GroupMembershipContext:
    group: Group
    user: User
    membership: GroupMembership | None


@dataclass
class EditGroupMembershipContext:
    group: Group
    user: User
    membership: GroupMembership
    new_roles: list[GroupMembershipRoles]


def _get_user(request, userid) -> User | None:
    user_service = request.find_service(name="user")

    if userid == "me":
        if request.authenticated_userid:
            return user_service.fetch(request.authenticated_userid)

        return None

    try:
        return user_service.fetch(userid)
    except InvalidUserId:
        return None


def _get_group(request, pubid) -> Group | None:
    group_service = request.find_service(name="group")
    return group_service.fetch(pubid)


def _get_membership(request, group, user) -> GroupMembership | None:
    group_members_service = request.find_service(name="group_members")
    return group_members_service.get_membership(group, user)


def group_membership_api_factory(request) -> GroupMembershipContext:
    userid = request.matchdict["userid"]
    pubid = request.matchdict["pubid"]

    user = _get_user(request, userid)
    group = _get_group(request, pubid)
    membership = _get_membership(request, group, user)

    if not user:
        raise HTTPNotFound(f"User not found: {userid}")

    if not group:
        raise HTTPNotFound(f"Group not found: {pubid}")

    if not membership and request.method != "POST":
        raise HTTPNotFound(f"Membership not found: ({pubid}, {userid})")

    return GroupMembershipContext(group=group, user=user, membership=membership)

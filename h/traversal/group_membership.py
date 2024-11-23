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


def group_membership_api_factory(request) -> GroupMembershipContext:
    user_service = request.find_service(name="user")
    group_service = request.find_service(name="group")
    group_members_service = request.find_service(name="group_members")

    userid = request.matchdict["userid"]
    pubid = request.matchdict["pubid"]

    def get_user() -> User | None:
        if userid == "me":
            if request.authenticated_userid:
                return user_service.fetch(request.authenticated_userid)

            return None

        try:
            return user_service.fetch(userid)
        except InvalidUserId:
            return None

    user = get_user()

    if not user:
        raise HTTPNotFound(f"User not found: {userid}")

    group = group_service.fetch(pubid)

    if not group:
        raise HTTPNotFound(f"Group not found: {pubid}")

    membership = group_members_service.get_membership(group, user)

    if not membership and request.method != "POST":
        raise HTTPNotFound(f"Membership not found: ({pubid}, {userid})")

    return GroupMembershipContext(group=group, user=user, membership=membership)

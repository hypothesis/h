from dataclasses import dataclass
from typing import Optional

from h.models import Group, User


@dataclass
class GroupContext:
    """Context for a single (optional) group."""

    group: Optional[Group] = None


class GroupRoot:
    """Root factory for group routes."""

    def __init__(self, request):
        self.request = request
        self.group_service = request.find_service(name="group")

    def __getitem__(self, pubid_or_groupid):
        # Group could be `None` here!
        return GroupContext(group=self.group_service.fetch(pubid_or_groupid))


class GroupRequiredRoot(GroupRoot):
    """Root factory for routes dealing with groups which must exist."""

    def __getitem__(self, pubid_or_groupid):
        group_context = super().__getitem__(pubid_or_groupid)
        if group_context.group is None:
            raise KeyError()

        return group_context


def group_membership_api_factory(request):
    """Route feactory for the "api.group_member" route."""

    def get_group():
        group_service = request.find_service(name="group")
        pubid_or_groupid = request.matchdict["pubid"]
        return group_service.fetch(pubid_or_groupid)

    def get_user():
        userid = request.matchdict["userid"]

        if userid == "me":
            if not request.identity:
                return None

            userid = request.identity.user.userid

        user_service = request.find_service(name="user")
        return user_service.fetch(userid)

    return GroupMembershipContext(get_group(), get_user())


class GroupMembershipContext:
    """Context for group membership-related views."""

    def __init__(self, group: Group | None, user: User | None):
        self.group = group
        self.user = user


class EditGroupMembershipContext:
    def __init__(self, group: Group | None, user: User | None, role: str):
        self.group = group
        self.user = user
        self.role = role

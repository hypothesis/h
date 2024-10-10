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


class RemoveMemberRoot:
    def __init__(self, request):
        self.request = request
        self.group_service = request.find_service(name="group")
        self.user_service = request.find_service(name="user")

    def __getitem__(self, group_id, user_id):
        return RemoveMemberContext(
            self.group_service.fetch(group_id),
            self.user_service.fetch(user_id),
        )


class RemoveMemberContext:
    """The context class for the remove-group-member API."""

    def __init__(self, group: Group, user: User):
        self.group = group
        self.user = user


class EditMemberContext:
    """The context class for the edit-group-member API."""

    def __init__(self, group: Group, user: User, new_role: str):
        self.group = group
        self.user = user
        self.new_role = new_role

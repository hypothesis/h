from dataclasses import dataclass
from typing import Optional

from h.models import Group
from h.security import ACL
from h.traversal.root import RootFactory


class GroupRoot(RootFactory):
    """Root factory for group routes."""

    def __init__(self, request):
        super().__init__(request)
        self.group_service = request.find_service(name="group")

    def __getitem__(self, pubid_or_groupid):
        # Group could be `None` here!
        return GroupContext(group=self.group_service.fetch(pubid_or_groupid))

    @classmethod
    def __acl__(cls):
        return ACL.for_group()


class GroupRequiredRoot(GroupRoot):
    """Root factory for routes dealing with groups which must exist."""

    def __getitem__(self, pubid_or_groupid):
        group_context = super().__getitem__(pubid_or_groupid)
        if group_context.group is None:
            raise KeyError()

        return group_context


@dataclass
class GroupContext:
    """Context for a single (optional) group."""

    group: Optional[Group] = None

    def __acl__(self):
        return ACL.for_group(self.group)

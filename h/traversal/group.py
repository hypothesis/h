from dataclasses import dataclass
from typing import Optional

from pyramid.security import Allow

from h.auth import role
from h.models import Group
from h.traversal.root import RootFactory


class GroupRoot(RootFactory):
    """Root factory for group routes."""

    # Any logged in user may create a group
    __acl__ = [(Allow, role.User, "create")]

    def __init__(self, request):
        super().__init__(request)
        self.group_service = request.find_service(name="group")

    def __getitem__(self, pubid_or_groupid):
        # Group could be `None` here!
        return GroupContext(group=self.group_service.fetch(pubid_or_groupid))


class GroupRequiredRoot(GroupRoot):
    """
    Root factory for routes dealing with groups which must exist.

    FIXME: This class should return GroupContext objects, not Group objects.
    """

    def __getitem__(self, pubid_or_groupid):
        group_context = super().__getitem__(pubid_or_groupid)
        if group_context.group is None:
            raise KeyError()

        return group_context.group


@dataclass
class GroupContext:
    """Context for a single (optional) group."""

    group: Optional[Group] = None

    def __acl__(self):
        if self.group is None:
            # If there's no group then give "upsert" permission to users to
            # allow them to use the UPSERT endpoint to create a new group.
            return [(Allow, role.User, "upsert")]

        # If there is a group associated with the context, the "upsert" and
        # all other permissions are managed by the model
        return self.group.__acl__()

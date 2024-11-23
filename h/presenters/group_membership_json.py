from h.models import GroupMembershipRoles
from h.security import Permission
from h.traversal.group_membership import (
    EditGroupMembershipContext,
    GroupMembershipContext,
)


class GroupMembershipJSONPresenter:
    def __init__(self, request, membership):
        self.request = request
        self.membership = membership

    def asdict(self):
        membership_dict = {
            "authority": self.membership.group.authority,
            "userid": self.membership.user.userid,
            "username": self.membership.user.username,
            "display_name": self.membership.user.display_name,
            "roles": self.membership.roles,
            "actions": [],
        }

        if self.request.has_permission(
            Permission.Group.MEMBER_REMOVE,
            GroupMembershipContext(
                self.membership.group, self.membership.user, self.membership
            ),
        ):
            membership_dict["actions"].append("delete")

        for role in GroupMembershipRoles:
            if self.request.has_permission(
                Permission.Group.MEMBER_EDIT,
                EditGroupMembershipContext(
                    self.membership.group, self.membership.user, self.membership, [role]
                ),
            ):
                membership_dict["actions"].append(f"updates.roles.{role}")

        return membership_dict

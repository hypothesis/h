class GroupMembershipJSONPresenter:
    def __init__(self, membership):
        self.membership = membership

    def asdict(self):
        return {
            "authority": self.membership.group.authority,
            "userid": self.membership.user.userid,
            "username": self.membership.user.username,
            "display_name": self.membership.user.display_name,
            "roles": self.membership.roles,
        }

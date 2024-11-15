from functools import partial

from sqlalchemy import select

from h import session
from h.models import GroupMembership


class GroupMembersService:
    """A service for manipulating group membership."""

    def __init__(self, db, user_fetcher, publish):
        """
        Create a new GroupMembersService.

        :param db: the SQLAlchemy db object
        :param user_fetcher: a callable for fetching users by userid
        :param publish: a callable for publishing events
        """
        self.db = db
        self.user_fetcher = user_fetcher
        self.publish = publish

    def add_members(self, group, userids):
        """
        Add the users indicated by userids to this group's members.

        Any pre-existing members will not be affected.

        :type group: `h.models.group.Group`
        :param userids: list of userids to add to this group's membership
        """
        for userid in userids:
            self.member_join(group, userid)

    def update_members(self, group, userids):
        """
        Update this group's membership to be the list of users indicated by userids.

        The users indicated by userids will *replace* the members of this group.
        Any pre-existing member whose userid is not present in userids will
        be removed as a member.

        :type group: `h.models.group.Group`
        :param userids: the list of userids corresponding to users who should
                        be the members of this group
        """
        current_mem_ids = [member.userid for member in group.members]
        userids_for_removal = [
            mem_id for mem_id in current_mem_ids if mem_id not in userids
        ]

        for userid in userids:
            self.member_join(group, userid)

        for userid in userids_for_removal:
            self.member_leave(group, userid)

    def member_join(self, group, userid):
        """Add `userid` to the member list of `group`."""
        user = self.user_fetcher(userid)

        existing_membership = self.db.scalar(
            select(GroupMembership)
            .where(GroupMembership.user == user)
            .where(GroupMembership.group == group)
        )

        if existing_membership:
            # The user is already a member of the group.
            return

        self.db.add(GroupMembership(group=group, user=user))

        self.publish("group-join", group.pubid, userid)

    def member_leave(self, group, userid):
        """Remove `userid` from the member list of `group`."""
        user = self.user_fetcher(userid)

        matching_memberships = self.db.scalars(
            select(GroupMembership)
            .where(GroupMembership.group == group)
            .where(GroupMembership.user == user)
        ).all()

        if not matching_memberships:
            return

        for membership in matching_memberships:
            self.db.delete(membership)

        self.publish("group-leave", group.pubid, userid)


def group_members_factory(_context, request):
    """Return a GroupMembersService instance for the passed context and request."""
    user_service = request.find_service(name="user")
    return GroupMembersService(
        db=request.db,
        user_fetcher=user_service.fetch,
        publish=partial(_publish, request),
    )


def _publish(request, event_type, groupid, userid):
    request.realtime.publish_user(
        {
            "type": event_type,
            "session_model": session.model(request),
            "userid": userid,
            "group": groupid,
        }
    )

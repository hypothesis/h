import logging
from functools import partial

from sqlalchemy import func, nulls_first, or_, select

from h import session
from h.models import Group, GroupMembership, GroupMembershipRoles, User

log = logging.getLogger(__name__)


class ConflictError(Exception):
    """A conflicting group membership already exists in the DB."""


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

    def get_membership(self, group, user) -> GroupMembership | None:
        """Return `user`'s existing membership in `group`, if any."""
        return self.db.scalar(
            select(GroupMembership)
            .where(GroupMembership.group == group)
            .where(GroupMembership.user == user)
        )

    def get_memberships(
        self,
        group: Group,
        roles: list[GroupMembershipRoles] | None = None,
        offset=None,
        limit=None,
    ):
        """
        Return `group`'s memberships.

        If `roles` is None return all of `group`'s memberships.

        If `roles` is not None return only those memberships matching the given role(s).

        If multiple roles are given return all memberships matching *any* of
        the given roles.
        """
        query = (
            select(GroupMembership)
            .join(User)
            .where(GroupMembership.group == group)
            .order_by(nulls_first(GroupMembership.created), User.username)
        )

        if roles:
            query = query.where(
                or_(GroupMembership.roles.contains(role) for role in roles)  # type: ignore[arg-type]
            )

        if offset is not None:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        return self.db.scalars(query)

    def count_memberships(self, group: Group):
        """Return the number of memberships of `group`."""
        return self.db.scalar(
            select(func.count(GroupMembership.id)).where(GroupMembership.group == group)
        )

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

        for userid in userids:
            if userid not in current_mem_ids:
                self.member_join(group, userid)

        for userid in current_mem_ids:
            if userid not in userids:
                self.member_leave(group, userid)

    def member_join(self, group, userid, roles=None) -> GroupMembership:
        """
        Add `userid` to `group` with `roles` and return the resulting membership.

        If `roles=None` it will default to `[GroupMembershipRoles.MEMBER]`.

        If a membership matching `group`, `userid` and `roles` already exists
        in the DB it will just be returned.

        :raise ConflictError: if a membership already exists with the given
            group and userid but different roles
        """
        roles = roles or [GroupMembershipRoles.MEMBER]

        user = self.user_fetcher(userid)

        kwargs = {"roles": roles}

        if existing_membership := self.get_membership(group, user):
            for key, value in kwargs.items():
                if getattr(existing_membership, key) != value:
                    raise ConflictError(  # noqa: TRY003
                        "The user is already a member of the group, with conflicting membership attributes"  # noqa: EM101
                    )

            return existing_membership

        membership = GroupMembership(group=group, user=user, **kwargs)
        self.db.add(membership)

        # Flush the DB to generate SQL defaults for `membership` before logging it.
        self.db.flush()

        log.info("Added group membership: %r", membership)
        self.publish("group-join", group.pubid, userid)

        return membership

    def member_leave(self, group, userid):
        """Remove `userid` from the member list of `group`."""
        user = self.user_fetcher(userid)

        membership = self.get_membership(group, user)

        if not membership:
            return

        self.db.delete(membership)

        log.info("Deleted group membership: %r", membership)
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

import sqlalchemy as sa
from sqlalchemy import literal_column, select, union

from h.models import Group, GroupMembership
from h.models.group import ReadableBy
from h.util import group as group_util


class GroupService:
    def __init__(self, session, user_fetcher):
        """
        Create a new groups service.

        :param session: the SQLAlchemy session object
        :param user_fetcher: a callable for fetching users by userid
        :param publish: a callable for publishing events
        """
        self.session = session
        self.user_fetcher = user_fetcher

    def fetch(self, pubid_or_groupid):
        """
        Fetch a group using either a groupid or a pubid.

        :arg pubid_or_groupid: a string in either :mod:`~h.pubid` format
            or as :attr:`h.models.Group.groupid`
        :rtype: :class:`~h.models.Group` or ``None``
        """
        if group_util.is_groupid(pubid_or_groupid):
            return self.fetch_by_groupid(pubid_or_groupid)
        return self.fetch_by_pubid(pubid_or_groupid)

    def fetch_by_pubid(self, pubid):
        """Return a group with the given ``pubid`` or ``None``."""
        return self.session.query(Group).filter_by(pubid=pubid).one_or_none()

    def fetch_by_groupid(self, groupid):
        """
        Return a group with the given ``groupid`` or ``None``.

        :arg groupid: String in groupid format, e.g. ``group:foo@bar.com``.
            See :class:`~h.models.Group`
        :raises ValueError: if ``groupid`` is not a valid groupid.
            See :func:`h.util.group.split_groupid`
        :rtype: :class:`~h.models.Group` or ``None``
        """
        parts = group_util.split_groupid(groupid)
        authority = parts["authority"]
        authority_provided_id = parts["authority_provided_id"]

        return (
            self.session.query(Group)
            .filter_by(authority=authority)
            .filter_by(authority_provided_id=authority_provided_id)
            .one_or_none()
        )

    def filter_by_name(self, name=None):
        """
        Return a Query of all Groups, optionally filtered by name.

        If ``name`` is present, groups will be filtered by name. Filtering
        is case-insensitive and wildcarded. Otherwise, all groups will be
        retrieved.

        :rtype: sqlalchemy.orm.query.Query
        """
        filter_terms = []

        if name:
            filter_terms.append(sa.func.lower(Group.name).like(f"%{name.lower()}%"))

        return (
            self.session.query(Group)
            .filter(*filter_terms)
            .order_by(Group.created.desc())
        )

    def groupids_readable_by(self, user, group_ids=None):
        """
        Return a list of pubids for which the user has read access.

        If the passed-in user is ``None``, this returns the list of
        world-readable groups.

        If `group_ids` is specified, only the subset of groups from that list is
        returned. This is more efficient if the caller wants to know which
        groups from a specific list are readable by the user.

        :type user: `h.models.user.User`
        """
        # Very few groups are readable by world, query those separately
        readable_by_world_query = select(Group.pubid).where(
            Group.readable_by == ReadableBy.world
        )
        query = readable_by_world_query

        if user is not None:
            user_is_member_query = (
                select(Group.pubid)
                .join(GroupMembership)
                .where(
                    GroupMembership.user_id == user.id,
                    Group.readable_by == ReadableBy.members,
                )
            )
            # Union these with the world readable ones
            # We wrap a subquery around in case we need to apply the group_ids filter below
            query = select(
                union(readable_by_world_query, user_is_member_query).subquery()
            )

        if group_ids:
            query = query.where(literal_column("pubid").in_(group_ids))

        return self.session.scalars(query).all()

    def groupids_created_by(self, user):
        """
        Return a list of pubids which the user created.

        If the passed-in user is ``None``, this returns an empty list.

        :type user: `h.models.user.User` or None
        """
        if user is None:
            return []

        return [
            g.pubid for g in self.session.query(Group.pubid).filter_by(creator=user)
        ]


def groups_factory(_context, request):
    """Return a GroupService instance for the passed context and request."""
    user_service = request.find_service(name="user")
    return GroupService(session=request.db, user_fetcher=user_service.fetch)

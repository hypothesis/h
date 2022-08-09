from collections import defaultdict
from typing import List

import sqlalchemy as sa

from h.models import Group, User
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

    def groupids_readable_by(self, user: User, pubids_or_groupids=None):
        """
        Return a list of pubids for which the user has read access.

        If the passed-in user is `None`, this returns the list of
        world-readable groups.

        If `pubids_or_groupids` is specified, only the subset of groups from
        that list is returned. This is more efficient if the caller wants to
        know which groups from a specific list are readable by the user.
        """

        query = self.session.query(Group.pubid)

        readable = Group.readable_by == ReadableBy.world
        if user is None:
            query.filter(readable)
        else:
            readable_member = sa.and_(
                Group.readable_by == ReadableBy.members,
                Group.members.any(User.id == user.id),
            )
            query = query.filter(sa.or_(readable, readable_member))

        if pubids_or_groupids:
            query = self._group_filter(query, pubids_or_groupids)

        return [record.pubid for record in query]

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

    @classmethod
    def _group_filter(cls, query, pubids_or_groupids: List[str]):
        """
        Apply a filter to a query to efficiently limit it to certain groups.

        This works for a mixed list of pubids or groupids.
        """

        # We will build up filter clauses for a single efficient query
        clauses = []

        if pubids := [
            id_ for id_ in pubids_or_groupids if not group_util.is_groupid(id_)
        ]:
            clauses.append(Group.pubid.in_(pubids))

        if groupids := [
            id_ for id_ in pubids_or_groupids if group_util.is_groupid(id_)
        ]:
            by_authority = defaultdict(list)
            for parts in (group_util.split_groupid(groupid) for groupid in groupids):
                by_authority[parts["authority"]].append(parts["authority_provided_id"])

            # We'll probably only ever get called with a single authority, but
            # there's no harm in being able to support multiple
            for authority, authority_provided_ids in by_authority.items():
                clauses.append(
                    sa.and_(
                        Group.authority == authority,
                        Group.authority_provided_id.in_(authority_provided_ids),
                    )
                )

        return query.filter(sa.or_(*clauses))


def groups_factory(_context, request):
    """Return a GroupService instance for the passed context and request."""
    user_service = request.find_service(name="user")
    return GroupService(session=request.db, user_fetcher=user_service.fetch)

from dataclasses import dataclass
from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from h.models import AnnotationMetadata, AnnotationSlim, Group, GroupMembership, User


class BadDateFilter(Exception):
    """There is something wrong with the date filter provided."""


def date_match(column: sa.Column, spec: dict):
    """
    Get an SQL comparator for a date column based on dict spec.

    The dict can contain operators as keys and dates as values as per the
    following complete (but nonsensical) filter:

        {
            "gt": "2012-11-30",
            "gte": "2012-11-30",
            "lt": "2012-11-30",
            "lte": "2012-11-30",
            "eq": "2012-11-30",
            "ne": "2012-11-30",
        }

    :raises BadDateFilter: For unrecognised operators or no spec
    """
    if not spec:
        raise BadDateFilter(f"No spec given to filter '{column}' on")

    clauses = []

    for op_key, value in spec.items():
        if op_key == "gt":
            clauses.append(column > value)
        elif op_key == "gte":
            clauses.append(column >= value)
        elif op_key == "lt":
            clauses.append(column < value)
        elif op_key == "lte":
            clauses.append(column <= value)
        elif op_key == "eq":
            clauses.append(column == value)
        elif op_key == "ne":
            clauses.append(column != value)
        else:
            raise BadDateFilter(f"Unknown date filter operator: {op_key}")

    return sa.and_(*clauses)


@dataclass
class BulkAnnotation:
    username: str
    authority_provided_id: str
    metadata: dict


class BulkAnnotationService:
    """A service for retrieving annotations in bulk."""

    # Aliases to distinguish between different types of user
    _AUTHOR = sa.orm.aliased(User, name="author")
    _AUDIENCE = sa.orm.aliased(User, name="audience")

    def __init__(self, db_session: Session):
        """Initialise the service."""

        self._db = db_session

    # pylint: disable=too-many-arguments
    def annotation_search(
        self,
        authority: str,
        audience: dict,
        created: dict,
        limit=100000,
    ) -> List[BulkAnnotation]:
        """
        Get a list of annotations or rows viewable by an audience of users.

        :param authority: The authority to search by
        :param audience: A specification of how to find the users. e.g.
            {"username": [...]}
        :param created: A specification of how to filter the created date. e.g.
            {"gt": "2019-01-20", "lte": "2019-01-21"}
        :param limit: A limit of results to generate

        :raises BadDateFilter: For poorly specified date conditions
        """

        results = self._db.execute(
            self._search_query(authority, audience=audience, created=created).limit(
                limit
            )
        )

        return [
            BulkAnnotation(
                username=row.username,
                authority_provided_id=row.authority_provided_id,
                metadata=row.metadata,
            )
            for row in results.all()
        ]

    @classmethod
    def _search_query(cls, authority, audience, created) -> Select:
        """Generate a query which can then be executed to find annotations."""
        return (
            sa.select(
                [
                    cls._AUTHOR.username,
                    Group.authority_provided_id,
                    sa.func.coalesce(AnnotationMetadata.data, "{}").label("metadata"),
                ]
            )
            .select_from(AnnotationSlim)
            .join(cls._AUTHOR, cls._AUTHOR.id == AnnotationSlim.user_id)
            .join(Group, Group.id == AnnotationSlim.group_id)
            .outerjoin(AnnotationMetadata)
            .where(
                date_match(AnnotationSlim.created, created),
                AnnotationSlim.shared.is_(True),
                AnnotationSlim.deleted.is_(False),
                cls._AUTHOR.nipsa.is_(False),
                AnnotationSlim.moderated.is_(False),
                Group.id.in_(cls._audience_groups_subquery(authority, audience)),
            )
        )

    @classmethod
    def _audience_groups_subquery(cls, authority, audience):
        return (
            sa.select(Group.id)
            .distinct()
            .join(GroupMembership, GroupMembership.group_id == Group.id)
            .join(cls._AUDIENCE, GroupMembership.user_id == cls._AUDIENCE.id)
            .where(
                cls._AUDIENCE.username.in_(audience["username"]),
                cls._AUDIENCE.authority == authority,
            )
        )


def service_factory(_context, request) -> BulkAnnotationService:
    """Service factory for the bulk annotation service."""

    return BulkAnnotationService(db_session=request.db)

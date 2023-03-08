from typing import List, Union

import sqlalchemy as sa
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from h.models import Annotation, AnnotationModeration, Group, GroupMembership, User


class BadDateFilter(Exception):
    """There is something wrong with the date filter provided."""


class BadFieldSpec(Exception):
    """There is something wrong with the field you have specified."""


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


class BulkAnnotationService:
    """A service for retrieving annotations in bulk."""

    # Aliases to distinguish between different types of user
    _AUTHOR = sa.orm.aliased(User, name="author")
    _AUDIENCE = sa.orm.aliased(User, name="audience")

    # Acceptable values to pass in as `fields`
    _FIELDS = {
        "author.username": _AUTHOR.username,
        "group.authority_provided_id": Group.authority_provided_id,
    }

    def __init__(self, db_session: Session):
        """Initialise the service."""

        self._db = db_session

    # pylint: disable=too-many-arguments
    def annotation_search(
        self,
        authority: str,
        audience: dict,
        updated: dict,
        fields: list = None,
        limit=100000,
    ) -> Union[List[Annotation], Row]:
        """
        Get a list of annotations or rows viewable by an audience of users.

        Using a fields argument will switch the return type from annotation
        objects to row objects. This is more efficient if you only need a
        few fields but less convenient if you want many fields. Check the
        `_FIELDS` attribute for acceptable fields and names.

        :param authority: The authority to search by
        :param audience: A specification of how to find the users. e.g.
            {"username": [...]}
        :param updated: A specification of how to filter the updated date. e.g.
            {"gt": "2019-01-20", "lte": "2019-01-21"}
        :param fields: A list of string descriptions of fields to return
            instead of full annotation objects.
        :param limit: A limit of results to generate

        :raises BadDateFilter: For poorly specified date conditions
        :raises BadFieldSpec: For poorly specified fields
        """

        results = self._db.execute(
            self._search_query(
                authority, audience=audience, updated=updated, fields=fields
            ).limit(limit)
        )

        if fields is None:
            results = results.scalars()

        return results.all()

    @classmethod
    def _search_query(cls, authority, audience, updated, fields=None) -> Select:
        """Generate a query which can then be executed to find annotations."""

        if fields is None:
            query = sa.select(Annotation)
        else:
            query = sa.select(list(cls._field_names_to_columns(fields))).select_from(
                Annotation
            )

        # Updated
        query = query.where(date_match(Annotation.updated, updated))

        # Shared
        query = query.where(Annotation.shared.is_(True))

        # Deleted
        query = query.where(Annotation.deleted.is_(False))

        # Audience
        query = query.join(Group, Annotation.groupid == Group.pubid).where(
            Group.id.in_(cls._audience_groups_subquery(authority, audience))
        )

        # NIPSA
        query = query.join(
            cls._AUTHOR,
            cls._AUTHOR.username
            == sa.func.split_part(sa.func.split_part(Annotation.userid, "@", 1), ":", 2)
            and cls._AUTHOR.authority == authority,
        ).where(cls._AUTHOR.nipsa.is_(False))

        # Moderated
        query = query.outerjoin(AnnotationModeration).where(
            AnnotationModeration.id.is_(None)
        )

        return query

    @classmethod
    def _field_names_to_columns(cls, field_names):
        if not field_names:
            raise BadFieldSpec("Fields cannot be present but empty")

        for field_name in field_names:
            column = cls._FIELDS.get(field_name)
            if column is None:
                raise BadFieldSpec(f"Unrecognised field: {field_name}")
            yield column

    @classmethod
    def _audience_groups_subquery(cls, authority, audience):
        return (
            sa.select(Group.id)
            .distinct()
            .join(GroupMembership, GroupMembership.group_id == Group.id)
            .join(cls._AUDIENCE, GroupMembership.user_id == cls._AUDIENCE.id)
            .where(
                cls._AUDIENCE._username.in_(  # pylint:disable=protected-access
                    [
                        username.lower().replace(".", "")
                        for username in audience["username"]
                    ]
                ),
                cls._AUDIENCE.authority == authority,
            )
        )


def service_factory(_context, request) -> BulkAnnotationService:
    """Service factory for the bulk annotation service."""

    return BulkAnnotationService(db_session=request.db)

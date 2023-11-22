from dataclasses import dataclass
from typing import List

import sqlalchemy as sa
from sqlalchemy.orm import Session

from h.models import Annotation, Group
from h.services.bulk_api._helpers import date_match


@dataclass
class BulkGroup:
    authority_provided_id: str


class BulkGroupService:
    """A service for retrieving groups in bulk."""

    def __init__(self, db: Session):
        self._db = db

    def group_search(
        self, groups: List[str], annotations_created: dict
    ) -> List[BulkGroup]:
        """
        Get a list of groups.

        :param groups: List of "authority_provided_id" to filter groups by.
            The returned groups will be a subset of this list.
        :param annotations_created: Filter by groups with annotations created in this date range.

        :raises BadDateFilter: For poorly specified date conditions
        """

        query = (
            sa.select([Group.authority_provided_id])
            .join(Annotation, Group.pubid == Annotation.groupid)
            .group_by(Group.authority_provided_id)
            .where(
                date_match(Annotation.created, annotations_created),
                Group.authority_provided_id.in_(groups),
            )
        )
        results = self._db.scalars(query)
        return [BulkGroup(authority_provided_id=row) for row in results.all()]


def service_factory(_context, request) -> BulkGroupService:
    return BulkGroupService(db=request.db)

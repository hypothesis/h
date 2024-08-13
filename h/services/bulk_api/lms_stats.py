# pylint:disable=not-callable,use-implicit-booleaness-not-comparison-to-zero,singleton-comparison
from dataclasses import dataclass
from datetime import datetime
from enum import Flag, auto

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from h.models import Annotation, AnnotationMetadata, AnnotationSlim, Group, User


@dataclass
class AnnotationCounts:
    annotations: int
    replies: int
    page_notes: int
    last_activity: datetime

    assignment_id: str | None = None
    display_name: str | None = None
    userid: str | None = None


class CountsGroupBy(Flag):
    """Allowed values to group the queries by."""

    USER = auto()
    ASSIGNMENT = auto()


class BulkLMSStatsService:
    def __init__(self, db: Session, authorized_authority: str):
        self._db = db
        self._authorized_authority = authorized_authority

    def _annotation_query(
        self,
        groups: list[str],
        h_userids: list[str] | None = None,
        assignment_ids: list[str] | None = None,
    ):
        query = (
            select(
                AnnotationSlim,
                AnnotationMetadata.data,
                case(
                    # It has parents, it's a reply
                    (func.array_length(Annotation.references, 1) != None, "reply"),
                    # Not anchored, page note
                    (
                        func.jsonb_array_length(Annotation.target_selectors) == 0,
                        "page_note",
                    ),
                    # No annotation text, highlight
                    (func.length(Annotation.text) == 0, "highlight"),
                    # Anything else, an annotation
                    else_="annotation",
                ).label("type"),
            )
            .join(Annotation)
            .join(User, User.id == AnnotationSlim.user_id)
            .join(Group, Group.id == AnnotationSlim.group_id)
            .join(
                AnnotationMetadata,
                AnnotationSlim.id == AnnotationMetadata.annotation_id,
            )
            .where(
                # Visible annotations
                AnnotationSlim.deleted == False,
                AnnotationSlim.moderated == False,
                AnnotationSlim.shared == True,
                User.nipsa.is_(False),
                # Limit search to the groups from the current authority
                Group.authority == self._authorized_authority,
                # From the groups we are interested
                # Even if this is assignment centric an assignment
                # might expand over multiple groups if using sections/groups
                Group.authority_provided_id.in_(groups),
            )
        )
        if assignment_ids:
            query = query.where(
                AnnotationMetadata.data["lms"]["assignment"][
                    "resource_link_id"
                ].astext.in_(assignment_ids)
            )

        if h_userids:
            query = query.where(
                func.concat("acct:", User.username, "@", User.authority).in_(h_userids)
            )

        return query

    def _count_columns(self, counts_query) -> tuple:
        return (
            func.count(counts_query.c.id)
            .filter(counts_query.c.type == "annotation")
            .label("annotations"),
            func.count(counts_query.c.id)
            .filter(counts_query.c.type == "reply")
            .label("replies"),
            func.count(counts_query.c.id)
            .filter(counts_query.c.type == "page_note")
            .label("page_notes"),
            func.max(counts_query.c.created).label("last_activity"),
        )

    def get_annotation_counts(
        self,
        groups: list[str],
        group_by: CountsGroupBy,
        h_userids: list[str] | None = None,
        assignment_ids: list[str] | None = None,
    ) -> list[AnnotationCounts]:
        """
        Get basic stats per user for an LMS assignment.

        :param groups: List of "authority_provided_id" to filter groups by.
        :param group_by: By which column to aggregate the data.
        :param h_userids: List of User.userid to filter annotations by
        :param assignment_ids: ID of the assignment to filter annotations by
        """
        annos_query = self._annotation_query(
            groups, h_userids=h_userids, assignment_ids=assignment_ids
        ).cte("annotations")

        # Alias some columns
        query_assignment_id = annos_query.c.data["lms"]["assignment"][
            "resource_link_id"
        ].astext
        # Unfortunately all the magic around User.userid doesn't work in this context
        query_userid = func.concat("acct:", User.username, "@", User.authority)

        # What to group_by depending on the selection
        group_by_clause = {
            CountsGroupBy.USER: User.id,
            CountsGroupBy.ASSIGNMENT: query_assignment_id,
        }

        # What columns to include, depending on the group by
        group_by_select_columns = {
            CountsGroupBy.USER: (
                query_userid.label("userid"),
                User.display_name,
            ),
            CountsGroupBy.ASSIGNMENT: (query_assignment_id.label("assignment_id"),),
        }

        # What joins to include, depending on the group by
        group_by_select_joins = {
            CountsGroupBy.USER: ((annos_query, annos_query.c.user_id == User.id),),
            CountsGroupBy.ASSIGNMENT: [],
        }

        query = select(
            # Include the relevant columnns based on group_by
            *group_by_select_columns[group_by],
            # Always include the counts column
            *self._count_columns(annos_query)
        )

        # Apply relevant joins
        for join in group_by_select_joins[group_by]:
            query = query.join(*join)

        # And finally the group by
        query = query.group_by(group_by_clause[group_by])

        results = self._db.execute(query)
        return [
            AnnotationCounts(
                assignment_id=row.get("assignment_id"),
                userid=row.get("userid"),
                display_name=row.get("display_name"),
                annotations=row.annotations,
                replies=row.replies,
                page_notes=row.page_notes,
                last_activity=row.last_activity,
            )
            for row in results.mappings()
        ]


def service_factory(_context, request) -> BulkLMSStatsService:
    return BulkLMSStatsService(
        db=request.db,
        authorized_authority=request.identity.auth_client.authority,
    )

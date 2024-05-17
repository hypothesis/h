# pylint:disable=not-callable,use-implicit-booleaness-not-comparison-to-zero,singleton-comparison
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from h.models import Annotation, AnnotationMetadata, AnnotationSlim, Group, User


@dataclass
class _AnnotationCounts:
    annotations: int
    replies: int
    last_activity: datetime


@dataclass
class CountsByUser(_AnnotationCounts):
    display_name: str
    userid: str


@dataclass
class CountsByAssignment(_AnnotationCounts):
    assignment_id: str


class BulkLMSStatsService:
    def __init__(self, db: Session, authorized_authority: str):
        self._db = db
        self._authorized_authority = authorized_authority

    def _annotation_query(self, groups: list[str]):
        return (
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

    def get_counts_by_user(
        self, groups: list[str], assignment_id: str
    ) -> list[CountsByUser]:
        """
        Get basic stats per user for an LMS assignment.

        :param groups: List of "authority_provided_id" to filter groups by.
        :param assignment_id: ID of the assignment we are generating the stats for.
        """
        annos_query = (
            self._annotation_query(groups)
            .where(
                AnnotationMetadata.data["lms"]["assignment"]["resource_link_id"].astext
                == assignment_id,
            )
            .cte("annotations")
        )

        query = (
            select(
                User.display_name,
                # Unfortunately all the magic around User.userid doesn't work in this context
                func.concat("acct:", User.username, "@", User.authority).label(
                    "userid"
                ),
                func.count(annos_query.c.id)
                .filter(annos_query.c.type == "annotation")
                .label("annotations"),
                func.count(annos_query.c.id)
                .filter(annos_query.c.type == "reply")
                .label("replies"),
                func.max(annos_query.c.created).label("last_activity"),
            )
            .join(annos_query, annos_query.c.user_id == User.id)
            .group_by(User.id)
        )

        results = self._db.execute(query)
        return [
            CountsByUser(
                userid=row.userid,
                display_name=row.display_name,
                annotations=row.annotations,
                replies=row.replies,
                last_activity=row.last_activity,
            )
            for row in results
        ]

    def get_counts_by_assignment(self, groups: list[str]) -> list[CountsByAssignment]:
        """
        Get basic stats per assignment for an LMS course.

        :param groups: List of "authority_provided_id" to filter groups by.
        """
        annos_query = self._annotation_query(groups).cte("annotations")
        query = select(
            annos_query.c.data["lms"]["assignment"]["resource_link_id"].astext.label(
                "assignment_id"
            ),
            func.count(annos_query.c.id)
            .filter(annos_query.c.type == "annotation")
            .label("annotations"),
            func.count(annos_query.c.id)
            .filter(annos_query.c.type == "reply")
            .label("replies"),
            func.max(annos_query.c.created).label("last_activity"),
        ).group_by(annos_query.c.data["lms"]["assignment"]["resource_link_id"].astext)

        results = self._db.execute(query)
        return [
            CountsByAssignment(
                assignment_id=row.assignment_id,
                annotations=row.annotations,
                replies=row.replies,
                last_activity=row.last_activity,
            )
            for row in results
        ]


def service_factory(_context, request) -> BulkLMSStatsService:
    return BulkLMSStatsService(
        db=request.db,
        authorized_authority=request.identity.auth_client.authority,
    )

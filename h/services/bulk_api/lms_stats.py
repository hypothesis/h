# pylint:disable=not-callable,use-implicit-booleaness-not-comparison-to-zero,singleton-comparison
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from h.models import Annotation, AnnotationMetadata, AnnotationSlim, Group, User


@dataclass
class AssignmentStats:
    display_name: str
    annotations: int
    replies: int
    last_activity: datetime


class BulkLMSStatsService:
    def __init__(self, db: Session, authorized_authority: str):
        self._db = db
        self._authorized_authority = authorized_authority

    def _annotation_type_select(self):
        """Build a select that tags each annotation row witht a type."""
        return select(
            AnnotationSlim,
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
        ).join(Annotation)

    def assignment_stats(
        self, groups: list[str], assignment_id: dict
    ) -> list[AssignmentStats]:
        """
        Get a list of groups.

        :param groups: List of "authority_provided_id" to filter groups by.
        :param assignment_id: ID of the assignment we are generating the stats for.
        """

        annotation_query = (
            self._annotation_type_select()
            .join(Group, Group.id == AnnotationSlim.group_id)
            .join(AnnotationMetadata)
            .where(
                # Visible annotations
                AnnotationSlim.deleted == False,
                AnnotationSlim.moderated == False,
                AnnotationSlim.shared == True,
                # Limit search to the groups from the current authority
                Group.authority == self._authorized_authority,
                # From the groups we are interested
                # Even if this is assignment centric an assigment
                # might expand over multiple groups if using sections/groups
                Group.authority_provided_id.in_(groups),
                # And finally the assignment ID
                AnnotationMetadata.data["lms"]["assignment"]["resource_link_id"].astext
                == assignment_id,
            )
        ).cte("annotations")

        query = (
            select(
                User.display_name,
                func.count(annotation_query.c.id)
                .filter(annotation_query.c.type == "annotation")
                .label("annotations"),
                func.count(annotation_query.c.id)
                .filter(annotation_query.c.type == "reply")
                .label("replies"),
                func.max(annotation_query.c.created).label("last_activity"),
            )
            .join(annotation_query, annotation_query.c.user_id == User.id)
            .group_by(User.id)
            .where(
                User.nipsa.is_(False),
            )
        )

        results = self._db.execute(query)
        return [
            AssignmentStats(
                display_name=row.display_name,
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

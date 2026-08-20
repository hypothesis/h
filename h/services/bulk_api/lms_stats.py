from dataclasses import dataclass
from datetime import datetime
from enum import Flag, auto

from sqlalchemy import and_, case, func, or_, select, true
from sqlalchemy.orm import Session

from h.models import (
    Annotation,
    AnnotationMetadata,
    AnnotationSlim,
    Checkpoint,
    Document,
    Group,
    User,
)


@dataclass
class AnnotationCounts:
    annotations: int
    replies: int
    page_notes: int
    last_activity: datetime

    assignment_id: str | None = None
    display_name: str | None = None
    userid: str | None = None

    # Populated only when the request includes `document_uri` (checkpoint
    # enabled assignments).
    checkpoint_annotations: int | None = None
    checkpoint_replies: int | None = None
    checkpoint_page_notes: int | None = None
    checkpoint_last_activity: datetime | None = None


class CountsGroupBy(Flag):
    """Allowed values to group the queries by."""

    USER = auto()
    ASSIGNMENT = auto()


class BulkLMSStatsService:
    def __init__(self, db: Session, authorized_authority: str):
        self._db = db
        self._authorized_authority = authorized_authority

    def _document_ids(self, document_uri: str) -> list[int]:
        """Every document `document_uri` resolves to in h."""
        return [doc.id for doc in Document.find_by_uris(self._db, [document_uri])]

    def get_checkpoint_state(
        self, groups: list[str], document_uri: str
    ) -> tuple[bool, datetime | None]:
        """
        Return (revealed, reveal_date) for `document_uri` across `groups`.
        """
        document_ids = self._document_ids(document_uri)
        if not document_ids:
            return False, None

        now = datetime.utcnow()  # noqa: DTZ003
        reveal_dates = self._db.scalars(
            select(Checkpoint.reveal_date)
            .join(Group, Group.id == Checkpoint.group_id)
            .where(Group.authority == self._authorized_authority)
            .where(Group.authority_provided_id.in_(groups))
            .where(Checkpoint.document_id.in_(document_ids))
            .where(Checkpoint.reveal_date.is_not(None))
            .where(Checkpoint.reveal_date <= now)
        ).all()
        if not reveal_dates:
            return False, None

        return True, min(reveal_dates)

    def _annotation_query(
        self,
        groups: list[str],
        h_userids: list[str] | None = None,
        assignment_ids: list[str] | None = None,
        due_date: datetime | None = None,
        checkpoint_document_ids: list[int] | None = None,
    ):
        if checkpoint_document_ids:
            # A checkpoint is a (group, document) pair, so each annotation is
            # judged against the reveal of *its own* group: on a group set the
            # same assignment is revealed per group, at different times.
            #
            # A NULL reveal_date (not revealed, or no checkpoint for the group)
            # leaves everything in the first phase. A reveal_date in the future
            # needs no special case: nothing can have been created after it yet.
            in_checkpoint = or_(
                Checkpoint.reveal_date.is_(None),
                AnnotationSlim.created <= Checkpoint.reveal_date,
            ).label("in_checkpoint")
        else:
            in_checkpoint = true().label("in_checkpoint")

        query = (
            select(
                AnnotationSlim,
                AnnotationMetadata.data,
                in_checkpoint,
                case(
                    # It has parents, it's a reply
                    (func.array_length(Annotation.references, 1) != None, "reply"),  # noqa: E711
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
            .outerjoin(
                Checkpoint,
                and_(
                    Checkpoint.group_id == AnnotationSlim.group_id,
                    Checkpoint.document_id.in_(checkpoint_document_ids or []),
                ),
            )
            .where(
                # Visible annotations
                AnnotationSlim.deleted == False,  # noqa: E712
                AnnotationSlim.moderated == False,  # noqa: E712
                AnnotationSlim.shared == True,  # noqa: E712
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

        if due_date:
            query = query.where(AnnotationSlim.created <= due_date)

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
            func.count(counts_query.c.id)
            .filter(counts_query.c.type == "annotation", counts_query.c.in_checkpoint)
            .label("checkpoint_annotations"),
            func.count(counts_query.c.id)
            .filter(counts_query.c.type == "reply", counts_query.c.in_checkpoint)
            .label("checkpoint_replies"),
            func.count(counts_query.c.id)
            .filter(counts_query.c.type == "page_note", counts_query.c.in_checkpoint)
            .label("checkpoint_page_notes"),
            func.max(counts_query.c.created)
            .filter(counts_query.c.in_checkpoint)
            .label("checkpoint_last_activity"),
        )

    def get_annotation_counts(  # noqa: PLR0913
        self,
        groups: list[str],
        group_by: CountsGroupBy,
        h_userids: list[str] | None = None,
        assignment_ids: list[str] | None = None,
        document_uri: str | None = None,
        due_date: datetime | None = None,
    ) -> list[AnnotationCounts]:
        """
        Get basic stats per user for an LMS assignment.

        :param groups: List of "authority_provided_id" to filter groups by.
        :param group_by: By which column to aggregate the data.
        :param h_userids: List of User.userid to filter annotations by
        :param assignment_ids: ID of the assignment to filter annotations by
        :param document_uri: The assignment's document URI. When given, the
            checkpoint_* fields are also populated on each result. Only
            meaningful for a single assignment per call — a checkpoint is a
            (group, document) pair, so mixing several assignments'
            `assignment_ids` under one `document_uri` would silently produce
            a bucketing that only makes sense for one of them.
        :param due_date: Optional upper bound on `created`, applied to every
            count above (not just the checkpoint_* subset).
        """
        if document_uri and (not assignment_ids or len(assignment_ids) != 1):
            raise ValueError(
                "document_uri requires assignment_ids to identify exactly one"
                " assignment: a checkpoint's reveal_date is only meaningful"
                " for a single (group, document) pair, not a mix of"
                " assignments."
            )

        annos_query = self._annotation_query(
            groups,
            h_userids=h_userids,
            assignment_ids=assignment_ids,
            due_date=due_date,
            checkpoint_document_ids=(
                self._document_ids(document_uri) if document_uri else None
            ),
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
            *self._count_columns(annos_query),
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
                checkpoint_annotations=(
                    row.checkpoint_annotations if document_uri else None
                ),
                checkpoint_replies=row.checkpoint_replies if document_uri else None,
                checkpoint_page_notes=(
                    row.checkpoint_page_notes if document_uri else None
                ),
                checkpoint_last_activity=(
                    row.checkpoint_last_activity if document_uri else None
                ),
            )
            for row in results.mappings()
        ]


def service_factory(_context, request) -> BulkLMSStatsService:
    return BulkLMSStatsService(
        db=request.db,
        authorized_authority=request.identity.auth_client.authority,
    )

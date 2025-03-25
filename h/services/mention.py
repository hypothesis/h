import logging
from collections import OrderedDict

from sqlalchemy import delete
from sqlalchemy.orm import Session, subqueryload

from h.models import Annotation, GroupMembership, Mention, User
from h.services.html import parse_html_links
from h.services.user import UserService
from h.util.markdown_render import MENTION_ATTRIBUTE, MENTION_USERID

MENTION_LIMIT = 5

logger = logging.getLogger(__name__)


class MentionService:
    """A service for managing user mentions."""

    def __init__(self, session: Session, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service

    def update_mentions(self, annotation: Annotation) -> None:
        self._session.flush()

        mentioning_user = self._user_service.fetch(annotation.userid)
        # NIPSA users do not send mentions
        if mentioning_user.nipsa:
            return

        mentioned_userids = list(
            OrderedDict.fromkeys(self._parse_userids(annotation.text)).keys()
        )
        if len(mentioned_userids) > MENTION_LIMIT:
            logger.warning(
                "Annotation %s has more than %s mentions",
                annotation.id,
                MENTION_LIMIT,
            )
            mentioned_userids = mentioned_userids[:MENTION_LIMIT]
        mentioned_users = (
            self._session.query(User)
            .filter(User.userid.in_(mentioned_userids))
            .options(subqueryload(User.memberships).subqueryload(GroupMembership.group))
            .all()
        )

        self._session.execute(
            delete(Mention).where(Mention.annotation_id == annotation.id)
        )

        for user in mentioned_users:
            # NIPSA users do not receive mentions
            if user.nipsa:
                continue
            # Only allow mentions if the annotation is in the public group
            # or the annotation is in one of mentioned user's groups
            if not (
                annotation.groupid == "__world__" or annotation.group in user.groups
            ):
                continue

            mention = Mention(
                annotation_id=annotation.id, user_id=user.id, username=user.username
            )
            self._session.add(mention)

    @staticmethod
    def _parse_userids(text: str) -> list[str]:
        links = parse_html_links(text)
        return [
            user_id
            for link in links
            if MENTION_ATTRIBUTE in link and (user_id := link.get(MENTION_USERID))
        ]


def factory(_context, request) -> MentionService:
    """Return a MentionService instance for the passed context and request."""
    return MentionService(
        session=request.db,
        user_service=request.find_service(name="user"),
    )

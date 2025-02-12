import logging
from collections import OrderedDict

from sqlalchemy import delete
from sqlalchemy.orm import Session

from h.models import Annotation, Mention
from h.services.html import parse_html_links
from h.services.user import UserService

MENTION_ATTRIBUTE = "data-hyp-mention"
MENTION_USERID = "data-userid"
MENTION_LIMIT = 5

logger = logging.getLogger(__name__)


class MentionService:
    """A service for managing user mentions."""

    def __init__(self, session: Session, user_service: UserService) -> None:
        self._session = session
        self._user_service = user_service

    def update_mentions(self, annotation: Annotation) -> None:
        self._session.flush()

        # Only shared annotations can have mentions
        if not annotation.shared:
            return
        mentioning_user = self._user_service.fetch(annotation.userid)
        # NIPSA users do not send mentions
        if mentioning_user.nipsa:
            return

        mentioned_userids = OrderedDict.fromkeys(self._parse_userids(annotation.text))
        mentioned_users = self._user_service.fetch_all(mentioned_userids)
        self._session.execute(
            delete(Mention).where(Mention.annotation_id == annotation.id)
        )

        for i, user in enumerate(mentioned_users):
            if i >= MENTION_LIMIT:
                logger.warning(
                    "Annotation %s has more than %s mentions",
                    annotation.id,
                    MENTION_LIMIT,
                )
                break
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

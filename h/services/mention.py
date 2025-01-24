import re

from sqlalchemy.orm import Session
import sqlalchemy as sa

from h.models import Annotation, Mention
from h.services.user import UserService

USERID_PAT = re.compile(r"data-userid=\"([^\"]+)\"")


class MentionService:
    """A service for managing user mentions."""

    def __init__(self, session: Session, user_service: UserService):
        self._session = session
        self._user_service = user_service

    def update_mentions(self, annotation: Annotation) -> None:
        self._session.flush()

        userids = set(self._parse_userids(annotation.text))
        users = self._user_service.fetch_all(userids)
        self._session.execute(
            sa.delete(Mention).where(Mention.annotation_id == annotation.id)
        )
        for user in users:
            mention = Mention(annotation_id=annotation.id, user_id=user.id)
            self._session.add(mention)

    @staticmethod
    def _parse_userids(text: str) -> list[str]:
        return USERID_PAT.findall(text)


def service_factory(_context, request) -> MentionService:
    """Return a MentionService instance for the passed context and request."""
    return MentionService(
        session=request.db, user_service=request.find_service(name="user")
    )

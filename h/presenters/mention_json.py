from typing import Any

from h.models import Mention
from h.util.user import format_userid


class MentionJSONPresenter:
    """Present a mention in the JSON format returned by API requests."""

    def __init__(self, mention: Mention):
        self._mention = mention

    def asdict(self) -> dict[str, Any]:
        return {
            "userid": self._mention.user.userid,
            "original_userid": format_userid(
                self._mention.username, self._mention.user.authority
            ),
            "username": self._mention.user.username,
            "display_name": self._mention.user.display_name,
            "link": self._mention.user.uri,
        }

from typing import Any

from h.models import Mention


class MentionJSONPresenter:
    """Present a mention in the JSON format returned by API requests."""

    def __init__(self, mention: Mention):
        self._mention = mention

    def asdict(self) -> dict[str, Any]:
        return {
            "userid": self._mention.user.userid,
            "username": self._mention.user.username,
            "display_name": self._mention.user.display_name,
            "link": self._mention.user.uri,
        }

from typing import Any

from pyramid.request import Request

from h.models import Mention
from h.util.datetime import utc_iso8601
from h.util.user import format_userid, get_user_url


class MentionJSONPresenter:
    """Present a mention in the JSON format returned by API requests."""

    def __init__(self, mention: Mention, request: Request):
        self._mention = mention
        self._request = request

    def asdict(self) -> dict[str, Any]:
        return {
            "userid": self._mention.user.userid,
            "original_userid": format_userid(
                self._mention.username, self._mention.user.authority
            ),
            "username": self._mention.user.username,
            "display_name": self._mention.user.display_name,
            "link": get_user_url(self._mention.user, self._request),
            "description": self._mention.user.description,
            "joined": utc_iso8601(self._mention.user.activation_date),
        }

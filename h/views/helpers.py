from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pyramid.security import remember

from h.accounts.events import LoginEvent

if TYPE_CHECKING:
    from pyramid.request import Request

    from h.models import User


def login(user: User, request: Request):
    """Log the browser session in to `user`'s account.

    The calling view must ensure that the returned headers are included in the
    response. For example if returning a response object:

        headers = login(user, request)
        return HTTPFound(location, headers=headers)

    If not directly returning a response object (for example when using a
    template renderer so the view just returns a dict of template variables):

        headers = login(user, request)
        request.response.headers.extend(headers)
        return template_variables

    """
    user.last_login_date = datetime.now(tz=UTC)  # type: ignore[assignment]
    request.registry.notify(LoginEvent(request, user))
    headers = remember(request, user.userid)
    return headers

from pyramid.request import Request

from h.models import User


def get_user_url(user: User, request: Request) -> str | None:
    if user.authority == request.default_authority:
        return request.route_url("stream.user_query", user=user.username)

    return None

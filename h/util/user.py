"""Some shared utility functions for manipulating user data."""

import re

from pyramid.request import Request

from h.exceptions import InvalidUserId


def split_user(userid):
    """
    Return the user and domain parts from the given user id as a dict.

    For example if userid is u'acct:seanh@hypothes.is' then return
    {'username': u'seanh', 'domain': u'hypothes.is'}'

    :raises InvalidUserId: if the given userid isn't a valid userid

    """
    match = re.match(r"^acct:([^@]+)@(.*)$", userid)
    if match:
        return {"username": match.groups()[0], "domain": match.groups()[1]}
    raise InvalidUserId(userid)


def format_userid(username, authority):
    return f"acct:{username}@{authority}"


def get_user_url(user, request: Request) -> str | None:
    if user.authority == request.default_authority:
        return request.route_url("activity.user_search", username=user.username)

    return None

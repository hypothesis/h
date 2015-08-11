"""Some shared utility functions."""
import re


def split_user(userid):
    """Return the user and domain parts from the given user id.

    For example if userid is u'acct:seanh@hypothes.is' then return
    (u'seanh', u'hypothes.is').

    """
    match = re.match(r'^acct:([^@]+)@(.*)$', userid)
    if match:
        return match.groups()
    # Passed username didn't match
    return None


def userid_from_username(username, request):
    """Return the full user ID for the given username.

    For example for username "seanh" return "acct:seanh@hypothes.is"
    (if we're at domain "hypothes.is").

    """
    return u"acct:{username}@{domain}".format(
        username=username, domain=request.domain)

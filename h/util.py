"""Some shared utility functions."""
import re


def split_user(userid):
    """Return the user and domain parts from the given user id.

    For example if userid is "acct:seanh@hypothes.is" then return
    ("seanh", "hypothes.is").

    """
    # Don't crash if people pass None to this function.
    # This is convenient, means calling code doesn't always need to test userid
    # for None.
    if not userid:
        return None

    match = re.match(r'^acct:([^@]+)@(.*)$', userid)
    if match:
        return match.groups()
    # Passed userid didn't match
    return None


def userid_from_username(username, request):
    """Return the full user ID for the given username.

    For example for username "seanh" return "acct:seanh@hypothes.is"
    (if we're at domain "hypothes.is").

    """
    return u"acct:{username}@{domain}".format(
        username=username, domain=request.domain)

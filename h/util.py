"""Some shared utility functions."""
import re


def split_user(username):
    """Return the user and domain parts from the given user account name.

    For example if username is "acct:seanh@hypothes.is" then return
    ("seanh", "hypothes.is").

    """
    return re.match(r'^acct:([^@]+)@(.*)$', username).groups()

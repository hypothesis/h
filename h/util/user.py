# -*- coding: utf-8 -*-
"""Some shared utility functions for manipulating user data."""
from __future__ import unicode_literals
import re


def split_user(userid):
    """Return the user and domain parts from the given user id as a dict.

    For example if userid is u'acct:seanh@hypothes.is' then return
    {'username': u'seanh', 'domain': u'hypothes.is'}'

    :raises ValueError: if the given userid isn't a valid userid

    """
    match = re.match(r"^acct:([^@]+)@(.*)$", userid)
    if match:
        return {"username": match.groups()[0], "domain": match.groups()[1]}
    raise ValueError("{userid} isn't a valid userid".format(userid=userid))

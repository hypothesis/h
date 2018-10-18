# -*- coding: utf-8 -*-
"""Some shared utility functions for manipulating group data."""
from __future__ import unicode_literals

import re


def split_groupid(groupid):
    """Return the ``authority_provided_id`` and ``authority`` from a ``groupid``

    For example if groupid is u'group:339ae9f33c@myauth.org' then return
    {'authority_provided_id': u'339ae9f33c', 'authority': u'myauth.org'}'

    :raises ValueError: if the given groupid isn't a valid groupid

    """
    match = re.match(r'^group:([^@]+)@(.*)$', groupid)
    if match:
        return {
            'authority_provided_id': match.groups()[0],
            'authority': match.groups()[1]
        }
    raise ValueError("{groupid} isn't a valid groupid".format(groupid=groupid))

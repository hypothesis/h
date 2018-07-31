# -*- coding: utf-8 -*-
"""Some shared utility functions for manipulating auth_client data."""
from __future__ import unicode_literals
import re


def split_client(clientid):
    """Return the ID and authority parts from the given clientid as a dict.

    For example if userid is u'client:04465aaa-8f73-11e8-91ca-8ba11742b240@hypothes.is' then return
    {'id': u'04465aaa-8f73-11e8-91ca-8ba11742b240', 'authority': u'hypothes.is'}'

    :raises ValueError: if the given clientid isn't a valid clientid

    """
    match = re.match(r'^client:([^@]+)@(.*)$', clientid)
    if match:
        return {
            'id': match.groups()[0],
            'authority': match.groups()[1]
        }
    raise ValueError("{clientid} isn't a valid clientid".format(clientid=clientid))

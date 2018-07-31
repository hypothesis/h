# -*- coding: utf-8 -*-
"""Some shared utility functions for manipulating auth_client data."""
from __future__ import unicode_literals
import re


def split_client(clientid):
    """Return the ID and authority parts from the given clientid as a dict.

    For example if userid is u'client:04465aaa-8f73-11e8-91ca-8ba11742b240@hypothes.is' then return
    {'id': u'04465aaa-8f73-11e8-91ca-8ba11742b240', 'authority': u'hypothes.is'}'

    :py:attr:`~h.models.user.AuthClient.id` must be a valid Python UUID

    :raises ValueError: if the given clientid isn't a valid clientid or if the
                        supplied AuthClient.id isn't a valid UUID

    """
    # Validates substring is a valid python UUID
    uuid_match = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    match = re.match(r'^client:(' + uuid_match + r')@(.*)$', clientid)
    if match:
        client = {
            'id': match.groups()[0],
            'authority': match.groups()[1]
        }

        if uuid_match:
            return client

    raise ValueError("{clientid} isn't a valid clientid".format(clientid=clientid))

# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def transform_annotation(event):
    """Add a {"nipsa": True} field on moderated annotations or those whose users are flagged."""
    payload = event.annotation_dict

    if _user_nipsa(event.request, payload):
        payload['nipsa'] = True


def _user_nipsa(request, payload):
    nipsa_service = request.find_service(name='nipsa')
    return 'user' in payload and nipsa_service.is_flagged(payload['user'])

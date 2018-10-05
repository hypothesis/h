# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def transform_annotation(event):
    """Add a {"nipsa": True} field on moderated annotations or those whose users are flagged."""
    annotation = event.annotation
    payload = event.annotation_dict

    nipsa = _user_nipsa(event.request, payload)
    if not event.request.feature('replace_nipsa_with_hidden_filter'):
        nipsa = nipsa or _annotation_moderated(event.request, annotation)

    if nipsa:
        payload['nipsa'] = True


def _user_nipsa(request, payload):
    nipsa_service = request.find_service(name='nipsa')
    return 'user' in payload and nipsa_service.is_flagged(payload['user'])


def _annotation_moderated(request, annotation):
    svc = request.find_service(name='annotation_moderation')
    return svc.hidden(annotation)

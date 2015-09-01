# -*- coding: utf-8 -*-

from annotator.auth import Consumer, User
from pyramid import httpexceptions

from h import i18n

_ = i18n.TranslationString


def get_user(request):
    """Create a User object for annotator-store."""
    userid = request.unauthenticated_userid
    if userid is not None:
        for principal in request.effective_principals:
            if principal.startswith('consumer:'):
                key = principal[9:]
                consumer = Consumer(key)
                return User(userid, consumer, False)
    return None


def validate_permissions(request, permissions):
    """Validate that the annotation's permissions are within the principals."""
    principals = request.effective_principals
    for reader in permissions.get('read', []):
        if reader not in principals:
            raise httpexceptions.HTTPUnauthorized(
                _('You are not authorized to write to this collection.')
            )

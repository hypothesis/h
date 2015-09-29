# -*- coding: utf-8 -*-

from pyramid import security

from annotator.auth import Consumer, User


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


def translate_annotation_principals(principals):
    """
    Translate a list of annotation principals to a list of pyramid principals.
    """
    result = set([])
    for principal in principals:
        # Ignore suspicious principals from annotations
        if principal.startswith('system.'):
            continue
        if principal == 'group:__world__':
            result.add(security.Everyone)
        elif principal == 'group:__authenticated__':
            result.add(security.Authenticated)
        else:
            result.add(principal)
    return list(result)

# -*- coding: utf-8 -*-

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

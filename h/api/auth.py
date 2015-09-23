# -*- coding: utf-8 -*-

from pyramid import security


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

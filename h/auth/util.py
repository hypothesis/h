# -*- coding: utf-8 -*-

from pyramid import security

from h import accounts
from h._compat import text_type


def effective_principals(userid, request):
    """
    Return the list of effective principals for the passed userid.

    Usually, we can leave the computation of the full set of effective
    principals to the pyramid authentication policy. Sometimes, however, it can
    be useful to discover the full set of effective principals for a userid
    other than the current authenticated userid. This function replicates the
    normal behaviour of a pyramid authentication policy and can be used for
    that purpose.
    """
    principals = set([security.Everyone])

    user = accounts.get_user(userid, request)

    if user is None:
        return list(principals)

    if user.admin:
        principals.add('group:__admin__')

    if user.staff:
        principals.add('group:__staff__')

    principals.update(group_principals(user))

    principals.add(security.Authenticated)

    principals.add(userid)

    return list(principals)


def group_principals(user):
    """Return any 'group:<pubid>' principals for the given user.

    Return a list of 'group:<pubid>' principals for the groups that the given
    user is a member of.

    :param user: the authorized user, as a User object
    :type user: h.accounts.models.User

    :rtype: list of strings

    """
    return ['group:{group.pubid}'.format(group=group) for group in user.groups]


def bearer_token(request):
    """
    Return the bearer token from the request's Authorization header.

    The "Bearer " prefix will be stripped from the token.

    If the request has no Authorization header or the Authorization header
    doesn't contain a bearer token, returns ''.

    :rtype: unicode
    """
    if request.headers.get('Authorization', '').startswith('Bearer '):
        return text_type(request.headers['Authorization'][len('Bearer '):])
    else:
        return u''

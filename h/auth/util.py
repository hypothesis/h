# -*- coding: utf-8 -*-

from pyramid import authorization
from pyramid import security

from h import accounts
from h.auth import role


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
        principals.add(role.Admin)

    if user.staff:
        principals.add(role.Staff)

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


def has_permission(request, context, userid, permission):
    """
    Return True if userid has permission on context object.

    Return True if the given userid has the given permission on the given
    context object, False otherwise.

    For example:

        if has_permission(request,
                          some_annotation,
                          'acct:philip@hypothes.is',
                          'read'):
            print 'philip can read this annotation'
        else:
            print "philip isn't allowed to read this annotation"

    """
    policy = request.registry.queryUtility(authorization.IAuthorizationPolicy)
    users_principals = effective_principals(userid, request)
    return bool(policy.permits(context, users_principals, permission))


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
        else:
            result.add(principal)
    return list(result)

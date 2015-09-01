# -*- coding: utf-8 -*-
def group_principals(request, user):
    """Return any 'group:<gid>' principals for the given user.

    Return a list of 'group:<gid>' principals for the groups that the given
    user is a member of.

    :param hashids: the request object
    :type hashids: pyramid.request.Request

    :param user: the authorized user, as a User object
    :type user: h.accounts.models.User

    :rtype: list of strings

    """
    hashids = request.hashids
    return ['group:{}'.format(g.hashid(hashids)) for g in user.groups]

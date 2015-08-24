def _authorized_for_group(effective_principals, group_hashid):
    if group_hashid == '__none__':
        return True
    elif group_hashid:
        required_principal = 'group:' + group_hashid
        return required_principal in effective_principals
    else:
        return True


def authorized_to_write_group(effective_principals, group_hashid):
    """Return True if effective_principals authorize writing to group.

    Return True if the given effective_principals authorize the request that
    owns them to write to the group identified by the given hashid. False
    otherwise.

    If group_hashid is falsy then always return True.

    """
    return _authorized_for_group(effective_principals, group_hashid)


def authorized_to_read_group(effective_principals, group_hashid):
    """Return True if effective_principals authorize reading group.

    Return True if the given effective_principals authorize the request that
    owns them to read annotations from the group identified by the given
    hashid. False otherwise.

    If group_hashid is falsy then always return True.

    """
    return _authorized_for_group(effective_principals, group_hashid)


def group_principals(user, hashids):
    """Return any 'group:<hashid>' principals for the given user.

    Return a list of 'group:<hashid>' principals for the groups that the given
    user is a member of.

    :param user: the authorized user, as a User object
    :type user: h.accounts.models.User

    :param hashids: the request.hashids object
    :type hashids: h.hashids.SimplerHashids

    :rtype: list of strings

    """
    return ['group:' + group.hashid(hashids) for group in user.groups]

def set_permissions(annotation):
    """Set the given annotation's permissions according to its group."""
    # For private annotations (visible only to the user who created them) the
    # client sends just the user's ID in the read permissions.
    is_private = (annotation['permissions']['read'] == [annotation['user']])

    if is_private:
        # The groups feature doesn't change the permissions for private
        # annotations at all.
        return

    group = annotation.get('group')
    if (not group) or (group == '__none__'):
        # The groups feature doesn't change the permissions for annotations
        # that don't belong to a group.
        return

    # If the annotation belongs to a group, we make it so that only users who
    # are members of that group can read the annotation.
    annotation['permissions']['read'] = ['group:' + group]


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


def authorized_to_read(effective_principals, annotation):
    """Return True if effective_principals authorize reading annotation.

    Return True if the given effective_principals authorize the request that
    owns them to read the given annotation. False otherwise.

    If the annotation belongs to a private group, this will return False if the
    authenticated user isn't a member of that group.

    """
    if 'group:__world__' in annotation['permissions']['read']:
        return True
    for principal in effective_principals:
        if principal in annotation['permissions']['read']:
            return True
    return False


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
    return ['group:__none__'] + [
        'group:' + group.hashid(hashids) for group in user.groups]

# -*- coding: utf-8 -*-
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

    group_principal = 'group:' + group

    # If the annotation belongs to a group, we make it so that only users who
    # are members of that group can read the annotation.
    annotation['permissions']['read'] = [group_principal]

    # If the annotation belongs to a group, we make it so that you have to be
    # both the user who created the annotation and a member of the annotation's
    # group to update the annotation.
    annotation['permissions']['update'] = [
        annotation['user'] + '~' + group_principal]


def group_principals(user, userid, hashids):
    """Return any 'group:<hashid>' principals for the given user.

    Return a list of 'group:<hashid>' principals for the groups that the given
    user is a member of.

    :param user: the authorized user, as a User object
    :type user: h.accounts.models.User

    :param hashids: the request.hashids object
    :type hashids: h.hashids.SimplerHashids

    :rtype: list of strings

    """
    principals = ['group:__none__']

    def group_principal(group):
        return 'group:' + group.hashid(hashids)

    principals.extend([group_principal(group) for group in user.groups])

    principals.extend([
        userid + '~' + group_principal(group) for group in user.groups])

    return principals

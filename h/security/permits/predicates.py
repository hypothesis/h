from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.security.permits.engine import predicate

# Identity things


@predicate()
def authenticated(identity, context):
    return bool(identity)


@predicate(requires=[authenticated])
def authenticated_user(identity, context):
    return bool(identity.user)


@predicate(requires=[authenticated_user])
def user_is_staff(identity, context):
    return identity.user.staff


@predicate(requires=[authenticated_user])
def user_is_admin(identity, context):
    return identity.user.admin


@predicate(requires=[authenticated])
def authenticated_client(identity, context):
    return bool(identity.auth_client)


@predicate(requires=[authenticated_client])
def authenticated_client_is_lms(identity, context):
    authority = identity.auth_client.authority

    return authority.startswith("lms.") and authority.endswith(".hypothes.is")


# Users


@predicate()
def user_found(identity, context):
    return hasattr(context, "user") and context.user


@predicate(requires=[authenticated_client, user_found])
def user_authority_matches_authenticated_client(identity, context):
    return context.user.authority == identity.auth_client.authority


# Annotations


@predicate()
def annotation_found(identity, context):
    return hasattr(context, "annotation") and context.annotation


@predicate(requires=[annotation_found])
def annotation_shared(identity, context):
    return context.annotation.shared


@predicate(requires=[annotation_found])
def annotation_not_shared(identity, context):
    return not context.annotation.shared


@predicate(requires=[annotation_found])
def annotation_live(identity, context):
    return not context.annotation.deleted


@predicate(requires=[authenticated_user, annotation_found])
def annotation_created_by_user(identity, context):
    return identity.user.userid == context.annotation.userid


# Groups


@predicate()
def group_found(identity, context):
    return hasattr(context, "group") and context.group


@predicate()
def group_not_found(identity, context):
    return not hasattr(context, "group") or not context.group


@predicate(requires=[group_found])
def group_writable_by_members(identity, context):
    return context.group.writeable_by == WriteableBy.members


@predicate(requires=[group_found])
def group_writable_by_world(identity, context):
    return context.group.writeable_by == WriteableBy.authority


@predicate(requires=[group_found])
def group_writable_by_authority(identity, context):
    return context.group.writeable_by == WriteableBy.authority


@predicate(requires=[group_found])
def group_readable_by_world(identity, context):
    return context.group.readable_by == ReadableBy.world


@predicate(requires=[group_found])
def group_readable_by_members(identity, context):
    return context.group.readable_by == ReadableBy.members


@predicate(requires=[group_found])
def group_joinable_by_authority(identity, context):
    return context.group.joinable_by == JoinableBy.authority


@predicate(requires=[authenticated_user, group_found])
def group_matches_user_authority(identity, context):
    return context.group.authority == identity.user.authority


@predicate(requires=[authenticated_user, group_found])
def group_created_by_user(identity, context):
    return context.group.creator and context.group.creator == identity.user


@predicate(requires=[authenticated_user, group_found])
def group_has_user_as_member(identity, context):
    return context.group in identity.user.groups


@predicate(requires=[authenticated_client, group_found])
def group_authority_matches_authenticated_client(identity, context):
    return context.user.authority == identity.group.authority

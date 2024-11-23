"""
Define authorization predicates.

These are functions which accept an `Identity` object and a context object and
return a truthy value. These represent building blocks of our permission map
which define when people do, or don't have permissions.

For example a predicate might define "group_created_by_user" which is only
true when a user is present, a group is present and the user created that
group.
"""

from itertools import chain

from h.models.group import GroupMembershipRoles, JoinableBy, ReadableBy, WriteableBy
from h.traversal import EditGroupMembershipContext, GroupMembershipContext


def requires(*parent_predicates):
    """
    Decorate a predicate to say it requires other predicates to be True first.

    :param *parent_predicates: A list of predicates that have to be true for
    this predicate to be true as well.
    """

    def decorator(function):
        function.requires = parent_predicates
        return function

    return decorator


# Identity things


def authenticated(identity, _context):
    return identity


# The `@requires` here means that this predicate needs `authenticate` to be
# True before it's True. It also avoids attribute errors if identity is None
@requires(authenticated)
def authenticated_user(identity, _context):
    return identity.user


@requires(authenticated_user)
def user_is_staff(identity, _context):
    return identity.user.staff


@requires(authenticated_user)
def user_is_admin(identity, _context):
    return identity.user.admin


@requires(authenticated)
def authenticated_client(identity, _context):
    return identity.auth_client


@requires(authenticated_client)
def authenticated_client_is_lms(identity, _context):
    authority = identity.auth_client.authority

    return authority.startswith("lms.") and authority.endswith(".hypothes.is")


# Users


def user_found(_identity, context):
    return hasattr(context, "user") and context.user


@requires(authenticated_client, user_found)
def user_authority_matches_authenticated_client(identity, context):
    return context.user.authority == identity.auth_client.authority


# Annotations


def annotation_found(_identity, context):
    return hasattr(context, "annotation") and context.annotation


@requires(annotation_found)
def annotation_shared(_identity, context):
    return context.annotation.shared


@requires(annotation_found)
def annotation_not_shared(_identity, context):
    return not context.annotation.shared


@requires(annotation_found)
def annotation_live(_identity, context):
    return not context.annotation.deleted


@requires(authenticated_user, annotation_found)
def annotation_created_by_user(identity, context):
    return identity.user.userid == context.annotation.userid


# Groups


def group_found(_identity, context):
    return hasattr(context, "group") and context.group


@requires(group_found)
def group_writable_by_members(_identity, context):
    return context.group.writeable_by == WriteableBy.members


@requires(group_found)
def group_writable_by_authority(_identity, context):
    return context.group.writeable_by == WriteableBy.authority


@requires(group_found)
def group_readable_by_world(_identity, context):
    return context.group.readable_by == ReadableBy.world


@requires(group_found)
def group_readable_by_members(_identity, context):
    return context.group.readable_by == ReadableBy.members


@requires(group_found)
def group_joinable_by_authority(_identity, context):
    return context.group.joinable_by == JoinableBy.authority


@requires(authenticated_user, group_found)
def group_has_user_as_owner(identity, context):
    return _group_has_user_as_role(identity, context, GroupMembershipRoles.OWNER)


@requires(authenticated_user, group_found)
def group_has_user_as_admin(identity, context):
    return _group_has_user_as_role(identity, context, GroupMembershipRoles.ADMIN)


@requires(authenticated_user, group_found)
def group_has_user_as_moderator(identity, context):
    return _group_has_user_as_role(identity, context, GroupMembershipRoles.MODERATOR)


def _group_has_user_as_role(identity, context, role):
    return any(
        membership.group.id == context.group.id and role in membership.roles
        for membership in identity.user.memberships
    )


@requires(authenticated_user, group_found)
def group_has_user_as_member(identity, context):
    return any(
        membership.group.id == context.group.id
        for membership in identity.user.memberships
    )


@requires(authenticated_user, group_found)
def group_matches_user_authority(identity, context):
    return context.group.authority == identity.user.authority


@requires(authenticated_client, group_found)
def group_matches_authenticated_client_authority(identity, context):
    return context.group.authority == identity.auth_client.authority


@requires(authenticated_user, group_found)
def group_member_remove(identity, context: GroupMembershipContext):
    def get_authenticated_users_membership():
        """Return the authenticated user's membership of the target group."""
        for membership in identity.user.memberships:
            if membership.group.id == context.group.id:
                return membership

        return None

    authenticated_users_membership = get_authenticated_users_membership()

    if not authenticated_users_membership:
        # You can't remove anyone from a group you're not a member of.
        return False

    if identity.user.userid == context.user.userid:
        # Any member can remove themselves from a group.
        return True

    if "owner" in context.membership.roles or "admin" in context.membership.roles:
        # Only owners can remove admins or other owners.
        return "owner" in authenticated_users_membership.roles

    if "moderator" in context.membership.roles:
        # Owners and admins can remove moderators.
        return (
            "owner" in authenticated_users_membership.roles
            or "admin" in authenticated_users_membership.roles
        )

    # Owners, admins and moderators can remove plain members.
    return (
        "owner" in authenticated_users_membership.roles
        or "admin" in authenticated_users_membership.roles
        or "moderator" in authenticated_users_membership.roles
    )


@requires(authenticated_user, group_found)
def group_member_edit(
    identity, context: EditGroupMembershipContext
):  # pylint:disable=too-many-return-statements,too-complex
    old_roles = context.membership.roles
    new_roles = context.new_roles

    def get_authenticated_users_roles():
        """Return the authenticated users roles in the target group."""
        for membership in identity.user.memberships:
            if membership.group.id == context.group.id:
                return membership.roles

        return None

    authenticated_users_roles = get_authenticated_users_roles()

    if not authenticated_users_roles:
        return False

    if identity.user.userid == context.user.userid:
        if GroupMembershipRoles.OWNER in authenticated_users_roles:
            # Owners can change their own role to anything.
            return True

        if GroupMembershipRoles.ADMIN in authenticated_users_roles:
            # Admins can change their own role to anything but admin.
            return GroupMembershipRoles.OWNER not in new_roles

        if GroupMembershipRoles.MODERATOR in authenticated_users_roles:
            # Moderators can change their own role to anything but owner or admin.
            return (
                GroupMembershipRoles.OWNER not in new_roles
                and GroupMembershipRoles.ADMIN not in new_roles
            )

        return False

    if GroupMembershipRoles.OWNER in authenticated_users_roles:
        # Owners can change any other member's role to any role.
        return True

    if GroupMembershipRoles.ADMIN in authenticated_users_roles:
        # Admins can change the role of anyone but owners or admins to anything
        # but owner or admin.
        if (
            GroupMembershipRoles.OWNER in old_roles + new_roles
            or GroupMembershipRoles.ADMIN in old_roles + new_roles
        ):
            return False

        return True

    return False


def resolve_predicates(mapping):
    """
    Expand predicates with requirements into concrete lists of predicates.

    This takes a permission map which contains predicates which reference
    other ones (using `@requires`), and converts each clause to include the
    parents in parent first order. This means any parent which is referred to
    by a predicate is executed before it, and no predicate appears more than once.
    """

    return {
        key: [_expand_clause(clause) for clause in clauses]
        for key, clauses in mapping.items()
    }


def _expand_clause(clause):
    """Generate all of the predicates + parents in a clause without dupes."""

    seen_before = set()
    # The chain.from_iterable here flattens nested iterables
    return list(
        chain.from_iterable(
            _expand_predicate(predicate, seen_before) for predicate in clause
        )
    )


def _expand_predicate(predicate, seen_before):
    """Generate all of the parents and the predicate in parents first order."""

    if hasattr(predicate, "requires"):
        for parent in predicate.requires:
            yield from _expand_predicate(parent, seen_before)

    if predicate not in seen_before:
        seen_before.add(predicate)
        yield predicate

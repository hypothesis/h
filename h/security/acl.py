from pyramid import security
from pyramid.security import DENY_ALL, Allow

from h.auth import role
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.security.permissions import Permission


class ACL:
    @classmethod
    def for_user(cls, user):
        client_authority = "client_authority:{}".format(user.authority)

        # auth_clients with the same authority as the user may update the user
        yield Allow, client_authority, Permission.User.UPDATE
        yield Allow, client_authority, Permission.User.READ

        # This is for inheriting security policies... do we inherit?
        yield DENY_ALL

    @classmethod
    def for_group(cls, group=None):
        # Any logged in user may create a group
        yield Allow, role.User, Permission.Group.CREATE

        if group:
            # Most permissions are contextual based on group
            yield from cls._for_group(group)
        else:
            # If and only if there's no group then give UPSERT permission to
            # users to allow them  to create a new group. Upserting an
            # existing group is a different
            yield Allow, role.User, Permission.Group.UPSERT

        yield DENY_ALL

    @classmethod
    def _for_group(cls, group):
        # This principal is given to clients which log in using an OAuth client
        # and secret to a particular authority
        client_authority_principal = f"client_authority:{group.authority}"
        # Given to logged in users to the authority they belong in
        in_authority_principal = f"authority:{group.authority}"
        # Logged in users are given group principals for all of their groups
        in_group_principal = f"group:{group.pubid}"

        if group.joinable_by == JoinableBy.authority:
            yield Allow, in_authority_principal, Permission.Group.JOIN

        if group.writeable_by == WriteableBy.authority:
            yield Allow, in_authority_principal, Permission.Group.WRITE
        elif group.writeable_by == WriteableBy.members:
            yield Allow, in_group_principal, Permission.Group.WRITE

        if group.readable_by == ReadableBy.members:
            yield Allow, in_group_principal, Permission.Group.READ
            yield Allow, in_group_principal, Permission.Group.MEMBER_READ
            yield Allow, in_group_principal, Permission.Group.FLAG

        elif group.readable_by == ReadableBy.world:
            yield Allow, security.Everyone, Permission.Group.READ
            yield Allow, security.Everyone, Permission.Group.MEMBER_READ
            # Any logged in user should be able to flag things they can see
            yield Allow, security.Authenticated, Permission.Group.FLAG

        # auth_clients with matching authority
        yield Allow, client_authority_principal, Permission.Group.READ
        yield Allow, client_authority_principal, Permission.Group.MEMBER_READ
        yield Allow, client_authority_principal, Permission.Group.MEMBER_ADD
        yield Allow, client_authority_principal, Permission.Group.ADMIN

        # Those with the admin or staff role should be able to admin/edit any
        # group
        yield Allow, role.Staff, Permission.Group.ADMIN
        yield Allow, role.Admin, Permission.Group.ADMIN

        if group.creator:
            yield Allow, group.creator.userid, Permission.Group.ADMIN
            yield Allow, group.creator.userid, Permission.Group.MODERATE
            yield Allow, group.creator.userid, Permission.Group.UPSERT

    @classmethod
    def for_annotation(cls, annotation):
        """Return a Pyramid ACL for this annotation.

        :param annotation: Annotation in question
        """
        yield Allow, security.Authenticated, Permission.Annotation.CREATE

        if annotation:
            if annotation.shared:
                yield from cls._for_shared_annotation(annotation)
            else:
                yield from cls._for_private_annotation(annotation)

            if not annotation.deleted:
                # The user who created the annotation always has the these permissions
                yield Allow, annotation.userid, Permission.Annotation.UPDATE
                yield Allow, annotation.userid, Permission.Annotation.DELETE

        yield DENY_ALL

    @classmethod
    def _for_private_annotation(cls, annotation):
        yield Allow, annotation.userid, Permission.Annotation.READ_REALTIME_UPDATES

        if not annotation.deleted:
            yield Allow, annotation.userid, Permission.Annotation.READ

            # Flagging one's own private annotations is nonsensical,
            # but from an authz perspective, allowed. It is up to services/views
            # to handle these situations appropriately
            yield Allow, annotation.userid, Permission.Annotation.FLAG

    @classmethod
    def _for_shared_annotation(cls, annotation):
        # If an annotation is shared then we derive our permissions based on
        # what the user is allowed to do in the group
        permission_map = {
            Permission.Group.READ: [
                Permission.Annotation.READ,
                Permission.Annotation.READ_REALTIME_UPDATES,
            ],
            Permission.Group.FLAG: [Permission.Annotation.FLAG],
            Permission.Group.MODERATE: [Permission.Annotation.MODERATE],
        }

        if annotation.deleted:
            # For deleted annotations the only thing you can do is be notified
            # that it's been deleted
            permission_map = {
                Permission.Group.READ: [Permission.Annotation.READ_REALTIME_UPDATES]
            }

        acls = ACL.for_group(annotation.group)

        for action, principal, permission in acls:
            try:
                for mapped_permission in permission_map.get(permission, []):
                    yield action, principal, mapped_permission

            except TypeError:
                # Things like Pyramid's "ALL_PERMISSIONS" can't be hashed or
                # mapped
                continue

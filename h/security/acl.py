from pyramid import security
from pyramid.security import Allow

from h.auth import role
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.security.permissions import Permission


class ACL:
    @classmethod
    def for_group(cls, group):
        # This principal is given to clients which log in using an OAuth client
        # and secret to a particular authority
        client_authority_principal = f"client_authority:{group.authority}"
        # Given to logged in users to the authority they belong in
        in_authority_principal = f"authority:{group.authority}"
        # Logged in users are given group principals for all of their groups
        in_group_principal = f"group:{group.pubid}"

        # General permissions ---------------------------------------------- #

        if group.joinable_by == JoinableBy.authority:
            yield Allow, in_authority_principal, Permission.Group.JOIN

        if group.writeable_by == WriteableBy.authority:
            yield Allow, in_authority_principal, Permission.Group.WRITE
        elif group.writeable_by == WriteableBy.members:
            yield Allow, in_group_principal, Permission.Group.WRITE

        if group.creator:
            yield Allow, group.creator.userid, Permission.Group.MODERATE
            # The creator may update this group in an upsert context
            yield Allow, group.creator.userid, Permission.Group.UPSERT

        # auth_clients that have the same authority as the target group
        # may add members to it
        yield Allow, client_authority_principal, Permission.Group.MEMBER_ADD

        # Read permissions ------------------------------------------------ #

        if group.readable_by == ReadableBy.members:
            yield Allow, in_group_principal, Permission.Group.READ
            yield Allow, in_group_principal, Permission.Group.MEMBER_READ
            yield Allow, in_group_principal, Permission.Group.FLAG
        elif group.readable_by == ReadableBy.world:
            yield Allow, security.Everyone, Permission.Group.READ
            yield Allow, security.Everyone, Permission.Group.MEMBER_READ
            # Any logged in user should be able to flag things they can see
            yield Allow, security.Authenticated, Permission.Group.FLAG

        # auth_clients with matching authority should be able to read the group
        # and it's members
        yield Allow, client_authority_principal, Permission.Group.READ
        yield Allow, client_authority_principal, Permission.Group.MEMBER_READ

        # Group edit permissions ------------------------------------------- #

        # auth_clients that have the same authority as this group
        # should be allowed to update it
        yield Allow, client_authority_principal, Permission.Group.ADMIN

        # Those with the admin or staff role should be able to admin/edit any
        # group
        yield Allow, role.Staff, Permission.Group.ADMIN
        yield Allow, role.Admin, Permission.Group.ADMIN

        if group.creator:
            # The creator of the group should be able to update it
            yield Allow, group.creator.userid, Permission.Group.ADMIN

        yield security.DENY_ALL

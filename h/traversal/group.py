from pyramid.security import Allow

from h.auth import role
from h.traversal.organization import OrganizationContext
from h.traversal.roots import RootFactory


class GroupRoot(RootFactory):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.GroupContext`.

    FIXME: This class should return GroupContext objects, not Group objects.

    """

    __acl__ = [(Allow, role.User, "create")]  # Any authn'd user may create a group

    def __init__(self, request):
        super().__init__(request)
        self.group_service = request.find_service(name="group")

    def __getitem__(self, pubid_or_groupid):
        group = self.group_service.fetch(pubid_or_groupid)
        if group is None:
            raise KeyError()
        return group


class GroupContext:
    """Context for group-based views."""

    def __init__(self, group, request):
        self.request = request
        self.group = group
        self.links_service = self.request.find_service(name="group_links")

    @property
    def id(self):
        return self.group.pubid  # Web-facing unique ID for this resource

    @property
    def links(self):
        return self.links_service.get_all(self.group)

    @property
    def organization(self):
        if self.group.organization is not None:
            return OrganizationContext(self.group.organization, self.request)
        return None


class GroupUpsertRoot(RootFactory):
    """
    Root factory for group "UPSERT" API

    This Root can support a route in which the traversal's ``__getitem__``
    will attempt a lookup but will not raise if that fails.

    This is to allow a single route that can accept and update an existing group
    OR create a new one.
    """

    __acl__ = GroupRoot.__acl__

    def __init__(self, request):
        super().__init__(request)
        self._group_root = GroupRoot(request)

    def __getitem__(self, pubid_or_groupid):
        try:
            group = self._group_root[pubid_or_groupid]
        except KeyError:
            group = None

        return GroupUpsertContext(group=group, request=self.request)


class GroupUpsertContext:
    """Context for group UPSERT"""

    def __init__(self, group, request):
        self._request = request
        self.group = group

    def __acl__(self):
        """
        Get the ACL from the group model or set "upsert" for all users in absence of model

        If there is a group model, get the ACL from there. Otherwise, return an
        ACL that sets the "upsert" permission for authenticated requests that have
        a real user associated with them via :attr:`h.auth.role.User`.

        The "upsert" permission is an unusual hybrid. It has a different meaning
        depending on the upsert situation.

        If there is no group associated with the context, the "upsert" permission
        should be given to all real users such that they may use the UPSERT endpoint
        to create a new group. However, if there is a group associated with the
        context, the "upsert" permission is managed by the model. The model only
        applies "upsert" for the group's creator. This will allow the endpoint to
        support updating a specific group (model), but only if the request's
        user should be able to update the group.
        """

        # TODO: This and ``GroupContext`` can likely be merged once ``GroupContext``
        # is used more resource-appropriately and returned by :class:`h.traversal.roots.GroupRoot`
        # during traversal
        if self.group is not None:
            return self.group.__acl__()
        return [(Allow, role.User, "upsert")]

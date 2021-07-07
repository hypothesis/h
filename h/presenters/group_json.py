from h.presenters.organization_json import OrganizationJSONPresenter
from h.traversal import OrganizationContext


class GroupJSONPresenter:
    """Present a group in the JSON format returned by API requests."""

    def __init__(self, group, request):
        self.links_service = request.find_service(name="group_links")
        self.group = group

        if group.organization is None:
            self.organization_context = None
        else:
            self.organization_context = OrganizationContext(group.organization, request)

    def asdict(self, expand=None):
        model = {
            "id": self.group.pubid,
            "links": self.links_service.get_all(self.group) or {},
            "groupid": self.group.groupid,
            "name": self.group.name,
            "organization": (
                self.organization_context.organization.pubid
                if self.organization_context
                else None
            ),
            "public": self.group.is_public,
            # DEPRECATED: TODO: remove from client
            "scoped": True if self.group.scopes else False,
            "type": self.group.type,
        }

        if expand:
            self._expand(model, expand)

        return model

    def _expand(self, model, expand):
        if "organization" in expand and self.organization_context:
            model["organization"] = OrganizationJSONPresenter(
                self.organization_context
            ).asdict()

        if "scopes" in expand:
            model["scopes"] = {
                # Groups in the DB have an `enforce_scope` property (default
                # True), but URL enforcement for annotations only happens if
                # there are scopes to restrict to. So the API value requires
                # both to be true.
                "enforced": bool(self.group.enforce_scope and self.group.scopes),
                # Format scopes to be the scope with a wild-card suffix so we
                # can make the scopes more granular later.
                "uri_patterns": [scope.scope + "*" for scope in self.group.scopes],
            }


class GroupsJSONPresenter:
    """Present a list of groups as JSON"""

    def __init__(self, groups, request):
        self.groups = groups
        self.request = request

    def asdicts(self, expand=None):
        return [
            GroupJSONPresenter(group, self.request).asdict(expand=expand)
            for group in self.groups
        ]

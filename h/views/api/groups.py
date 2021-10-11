from pyramid.httpexceptions import (
    HTTPBadRequest,
    HTTPConflict,
    HTTPNoContent,
    HTTPNotFound,
)

from h.i18n import TranslationString as _
from h.presenters import GroupJSONPresenter, GroupsJSONPresenter, UserJSONPresenter
from h.schemas.api.group import CreateGroupAPISchema, UpdateGroupAPISchema
from h.security import Permission
from h.views.api.config import api_config
from h.views.api.exceptions import PayloadError


@api_config(
    versions=["v1", "v2"],
    route_name="api.groups",
    request_method="GET",
    link_name="groups.read",
    description="Fetch the user's groups",
)
def groups(request):
    """Retrieve the groups for this request's user."""

    expand = request.GET.getall("expand") or []
    list_svc = request.find_service(name="group_list")

    all_groups = list_svc.request_groups(
        user=request.user,
        authority=request.params.get("authority"),
        document_uri=request.params.get("document_uri"),
    )

    all_groups = GroupsJSONPresenter(all_groups, request).asdicts(expand=expand)
    return all_groups


@api_config(
    versions=["v1", "v2"],
    route_name="api.groups",
    request_method="POST",
    permission=Permission.Group.CREATE,
    link_name="group.create",
    description="Create a new group",
)
def create(request):
    """Create a group from the POST payload."""
    appstruct = CreateGroupAPISchema(
        default_authority=request.default_authority,
        group_authority=request.effective_authority,
    ).validate(_json_payload(request))

    group_service = request.find_service(name="group")
    group_create_service = request.find_service(name="group_create")

    # Check for duplicate group
    groupid = appstruct.get("groupid", None)
    if groupid is not None:
        duplicate_group = group_service.fetch(pubid_or_groupid=groupid)
        if duplicate_group:
            raise HTTPConflict(
                _("group with groupid '{}' already exists").format(groupid)
            )

    group = group_create_service.create_private_group(
        name=appstruct["name"],
        userid=request.user.userid,
        description=appstruct.get("description", None),
        groupid=groupid,
    )
    return GroupJSONPresenter(group, request).asdict(expand=["organization", "scopes"])


@api_config(
    versions=["v1", "v2"],
    route_name="api.group",
    request_method="GET",
    permission=Permission.Group.READ,
    link_name="group.read",
    description="Fetch a group",
)
def read(context, request):
    """Fetch a group."""

    expand = request.GET.getall("expand") or []

    return GroupJSONPresenter(context.group, request).asdict(expand=expand)


@api_config(
    versions=["v1", "v2"],
    route_name="api.group",
    request_method="PATCH",
    permission=Permission.Group.EDIT,
    link_name="group.update",
    description="Update a group",
)
def update(context, request):
    """Update a group from a PATCH payload."""
    appstruct = UpdateGroupAPISchema(
        default_authority=request.default_authority,
        group_authority=request.effective_authority,
    ).validate(_json_payload(request))

    group_update_service = request.find_service(name="group_update")
    group_service = request.find_service(name="group")

    # Check for duplicate group
    groupid = appstruct.get("groupid", None)
    if groupid is not None:
        duplicate_group = group_service.fetch(pubid_or_groupid=groupid)
        if duplicate_group and (duplicate_group != context.group):
            raise HTTPConflict(
                _("group with groupid '{}' already exists").format(groupid)
            )

    group = group_update_service.update(context.group, **appstruct)

    return GroupJSONPresenter(group, request).asdict(expand=["organization", "scopes"])


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_upsert",
    request_method="PUT",
    permission=Permission.Group.UPSERT,
    link_name="group.create_or_update",
    description="Create or update a group",
)
def upsert(context, request):
    """
    Create or update a group from a PUT payload.

    If no group model is present in the passed ``context`` (on ``context.group``),
    treat this as a create action and delegate to ``create``.

    Otherwise, replace the existing group's resource properties entirely and update
    the object.

    :arg context:
    :type context: h.traversal.GroupUpsertContext
    """
    if context.group is None:
        return create(request)

    group = context.group

    # Because this is a PUT endpoint and not a PATCH, a full replacement of the
    # entire resource is expected. Thus, we're validating against the Create schema
    # here as we want to make sure properties required for a fresh object are present
    appstruct = CreateGroupAPISchema(
        default_authority=request.default_authority,
        group_authority=request.effective_authority,
    ).validate(_json_payload(request))

    group_update_service = request.find_service(name="group_update")
    group_service = request.find_service(name="group")

    # Check for duplicate group
    groupid = appstruct.get("groupid", None)
    if groupid is not None:
        duplicate_group = group_service.fetch(pubid_or_groupid=groupid)
        if duplicate_group and (duplicate_group != group):
            raise HTTPConflict(
                _("group with groupid '{}' already exists").format(groupid)
            )

    # Need to make sure every resource-defined property is present, as this
    # is meant as a full-resource-replace operation.
    # TODO: This may be better handled in the schema at some point
    update_properties = {
        "name": appstruct["name"],
        "description": appstruct.get("description", ""),
        "groupid": appstruct.get("groupid", None),
    }

    group = group_update_service.update(group, **update_properties)

    # Note that this view takes a ``GroupUpsertContext`` but uses a ``GroupContext`` here
    return GroupJSONPresenter(group, request).asdict(expand=["organization", "scopes"])


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_members",
    request_method="GET",
    link_name="group.members.read",
    description="Fetch all members of a group",
    permission=Permission.Group.READ,
)
def read_members(context, _request):
    """Fetch the members of a group."""
    return [UserJSONPresenter(user).asdict() for user in context.group.members]


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="DELETE",
    link_name="group.member.delete",
    description="Remove the current user from a group",
    is_authenticated=True,
)
def remove_member(context, request):
    """Remove a member from the given group."""
    # Currently, we only support removing the requesting user
    if request.matchdict.get("userid") == "me":
        userid = request.authenticated_userid
    else:
        raise HTTPBadRequest('Only the "me" user value is currently supported')

    group_members_service = request.find_service(name="group_members")
    group_members_service.member_leave(context.group, userid)

    return HTTPNoContent()


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_member",
    request_method="POST",
    link_name="group.member.add",
    permission=Permission.Group.MEMBER_ADD,
    description="Add the user in the request params to a group.",
)
def add_member(context, request):
    """
    Add a member to a given group.

    :raise HTTPNotFound: if the user is not found or if the use and group
      authorities don't match.
    """
    user_svc = request.find_service(name="user")
    group_members_svc = request.find_service(name="group_members")

    try:
        user = user_svc.fetch(request.matchdict["userid"])
    except ValueError as err:
        raise HTTPNotFound() from err

    if user is None:
        raise HTTPNotFound()

    if user.authority != context.group.authority:
        raise HTTPNotFound()

    group_members_svc.member_join(context.group, user.userid)

    return HTTPNoContent()


# @TODO This is a duplication of code in h.views.api — move to a util module
def _json_payload(request):
    """
    Return a parsed JSON payload for the request.

    :raises PayloadError: if the body has no valid JSON body
    """
    try:
        return request.json_body
    except ValueError as err:
        raise PayloadError() from err

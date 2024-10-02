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
from h.traversal import GroupContext
from h.views.api.config import api_config
from h.views.api.exceptions import PayloadError

DEFAULT_GROUP_TYPE = "private"


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

    group_type = appstruct.get("type", DEFAULT_GROUP_TYPE)

    kwargs = {
        "name": appstruct["name"],
        "userid": request.user.userid,
        "description": appstruct.get("description", None),
        "groupid": groupid,
    }

    if group_type == "private":
        method = group_create_service.create_private_group
    else:
        assert group_type in ("restricted", "open")
        kwargs["scopes"] = []

        if group_type == "restricted":
            method = group_create_service.create_restricted_group
        else:
            assert group_type == "open"
            method = group_create_service.create_open_group

    group = method(**kwargs)

    return GroupJSONPresenter(group, request).asdict(expand=["organization", "scopes"])


@api_config(
    versions=["v1", "v2"],
    route_name="api.group",
    request_method="GET",
    permission=Permission.Group.READ,
    link_name="group.read",
    description="Fetch a group",
)
def read(context: GroupContext, request):
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
def update(context: GroupContext, request):
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
    route_name="api.group_members",
    request_method="GET",
    link_name="group.members.read",
    description="Fetch all members of a group",
    permission=Permission.Group.READ,
)
def read_members(context: GroupContext, _request):
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
def remove_member(context: GroupContext, request):
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
def add_member(context: GroupContext, request):
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

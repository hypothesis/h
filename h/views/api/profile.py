from pyramid.httpexceptions import HTTPBadRequest

from h import session as h_session
from h.presenters import GroupsJSONPresenter
from h.security import Permission
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.profile",
    request_method="GET",
    link_name="profile.read",
    description="Fetch the user's profile",
)
def profile(request):
    authority = request.params.get("authority")
    return h_session.profile(request, authority)


@api_config(
    versions=["v1", "v2"],
    route_name="api.profile_groups",
    request_method="GET",
    link_name="profile.groups.read",
    description="Fetch the current user's groups",
)
def profile_groups(request):
    """
    Retrieve the groups for this request's user.

    Retrieve all groups for which the request's user is a member, regardless
    of type. Groups are sorted by (name, pubid).
    """

    expand = request.GET.getall("expand") or []
    list_svc = request.find_service(name="group_list")

    groups = list_svc.user_groups(user=request.user)
    groups_formatted = GroupsJSONPresenter(groups, request).asdicts(expand=expand)
    return groups_formatted


@api_config(
    versions=["v1", "v2"],
    route_name="api.profile",
    request_method="PATCH",
    permission=Permission.Profile.UPDATE,
    link_name="profile.update",
    description="Update a user's preferences",
)
def update_preferences(request):
    preferences = request.json_body.get("preferences", {})

    svc = request.find_service(name="user")
    # TODO: The following exception doesn't match convention for validation
    # used in other endpoints
    try:
        svc.update_preferences(request.user, **preferences)
    except TypeError as err:
        raise HTTPBadRequest(str(err)) from err

    return h_session.profile(request)

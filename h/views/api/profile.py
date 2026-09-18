from pyramid.httpexceptions import HTTPBadRequest

from h import session as h_session
from h.presenters import GroupsJSONPresenter
from h.schemas import ValidationError
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
    # TODO: The following exception doesn't match convention for validation  # noqa: FIX002, TD002, TD003
    # used in other endpoints
    try:
        # Enforce first-party authority for the EDU role survey. The survey is
        # only ever offered to first-party users, so only they can answer it:
        # without this a third-party account -- an LMS user who could never
        # have been shown the panel -- can PATCH an answer straight into the
        # column the HubSpot sync reads. This is only part of the eligibility
        # the read side applies; the feature flag and the EDU domain check land
        # with it.
        #
        # Inside the try on purpose: `preferences` is unvalidated JSON, so the
        # `in` raises TypeError for a non-mapping body such as
        # {"preferences": null}, which has to stay a 400.
        if (
            "instructor_survey_response" in preferences
            and request.user.authority != request.default_authority
        ):
            message = "instructor_survey_response is not available to this user"
            raise ValidationError(message)

        svc.update_preferences(request.user, **preferences)
    except TypeError as err:
        raise HTTPBadRequest(str(err)) from err

    return h_session.profile(request)

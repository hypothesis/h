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
        # Only take an answer to the EDU role survey from someone the survey is
        # actually for. The audience is decided by the same function the read
        # path uses, so someone who could never have been shown the panel -- a
        # third-party LMS account, a user whose email isn't at an educational
        # institution, anyone at all once the kill switch is off -- can't PATCH
        # an answer into the column the HubSpot sync reads, and a change to who
        # gets the survey moves the write path with it.
        #
        # `isinstance` first: `preferences` is unvalidated JSON, and without it
        # `in` is a substring test for a string body and raises TypeError for
        # {"preferences": null}. Those bodies belong to the `**preferences`
        # below, which turns them into the 400 they have always been.
        answering_survey = (
            isinstance(preferences, dict)
            and "instructor_survey_response" in preferences
        )

        if answering_survey:
            if not h_session.can_answer_edu_role_survey(request):
                # All-or-nothing on purpose: this rejects the whole PATCH, so
                # any other preference sent with it is not applied either. A
                # 400 that had silently applied half the body would be harder
                # to reason about than one that applied none of it, and the
                # client sends the survey answer on its own.
                message = "instructor_survey_response is not available to this user"
                raise ValidationError(message)

            if not h_session.show_edu_role_survey(request):
                # In the audience but not being asked, which can only mean they
                # have answered already. Drop the key instead of rejecting the
                # request: a retry after a lost response, or a dismissal in a
                # second sidebar still showing a profile from before the first
                # answer, is a no-op and not an error the user should see. Any
                # other preference in the same PATCH still applies. Once
                # show_edu_role_survey starts re-asking the people who dismissed
                # it, it returns True for them and this is skipped.
                #
                # Note this is second, so it can't stand in for the audience
                # check above: having answered before doesn't carry an answer
                # past the kill switch once it's off.
                #
                # The rule is "first answer wins", and that cuts both ways:
                # answer in one tab and the other tab's stale panel can't
                # overwrite it, but dismiss first and a later "instructor" from
                # a stale panel is dropped too, so the sync sees the dismissal.
                # Preferring a real answer over a dismissal would be a product
                # call, not a fix.
                #
                # "First" here is only as fine-grained as the read: the check
                # above and the write below aren't atomic, so two answers sent
                # in the same instant both see NULL and the second one wins.
                # That covers the stale-panel case this is for, which is tabs
                # minutes or hours apart, and not a genuine double submit. A
                # conditional UPDATE ... WHERE edu_role_survey_response IS NULL
                # would close it if the sync ever needs the stronger promise.
                preferences = {
                    key: value
                    for key, value in preferences.items()
                    if key != "instructor_survey_response"
                }

        svc.update_preferences(request.user, **preferences)
    except TypeError as err:
        raise HTTPBadRequest(str(err)) from err

    return h_session.profile(request)

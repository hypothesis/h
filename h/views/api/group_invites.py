from h.views.api.config import api_config

@api_config(
    versions=["v1", "v2"],
    route_name="api.group_invite",
    request_method="POST",
    link_name="group.invite.add",
    description="Create an invitation for a user to join a group",
    permission=Permission.Group.MEMBER_INVITE,
)
def create_invite(context: AddGroupMembershipContext, request):
    if context.user.authority != context.group.authority:
        raise HTTPNotFound()

    if request.body:
        appstruct = EditGroupMembershipAPISchema().validate(json_payload(request))
        roles = appstruct["roles"]
    else:
        # This doesn't mean the membership will be created with no roles:
        # default roles will be applied by the service.
        roles = None

    group_members_service = request.find_service(name="group_members")

    try:
        membership = group_members_service.member_join(
            context.group, context.user.userid, roles
        )
    except ConflictError as err:
        raise HTTPConflict(str(err)) from err

    return GroupMembershipJSONPresenter(request, membership).asdict()


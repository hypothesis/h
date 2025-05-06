from h.views.api.config import api_config
from h.security import Permission


@api_config(
    versions=["v1", "v2"],
    route_name="api.group_invites",
    request_method="GET",
    link_name="group.invites.read",
    description="Fetch a list of all a group's pending invites",
    permission=Permission.Group.READ,
)
def list_invites(context: GroupContext, request):
    group = context.group
    params = request.params
    page_number = params["page[number]"]
    page_size = params["page[size]"]
    offset = page_size * (page_number - 1)
    limit = page_size

    total = group_members_service.count_memberships(group)
    memberships = group_members_service.get_memberships(
        group, offset=offset, limit=limit
    )

    membership_dicts = [
        GroupMembershipJSONPresenter(request, membership).asdict()
        for membership in memberships
    ]

    return {"meta": {"page": {"total": total}}, "data": membership_dicts}


# @api_config(
#     versions=["v1", "v2"],
#     route_name="api.group_invite",
#     request_method="POST",
#     link_name="group.invite.add",
#     description="Create an invitation for a user to join a group",
#     permission=Permission.Group.MEMBER_INVITE,
# )
# def create_invite(context: AddGroupMembershipContext, request):
#     if context.user.authority != context.group.authority:
#         raise HTTPNotFound()

#     if request.body:
#         appstruct = EditGroupMembershipAPISchema().validate(json_payload(request))
#         roles = appstruct["roles"]
#     else:
#         # This doesn't mean the membership will be created with no roles:
#         # default roles will be applied by the service.
#         roles = None

#     group_members_service = request.find_service(name="group_members")

#     try:
#         membership = group_members_service.member_join(
#             context.group, context.user.userid, roles
#         )
#     except ConflictError as err:
#         raise HTTPConflict(str(err)) from err

#     return GroupMembershipJSONPresenter(request, membership).asdict()


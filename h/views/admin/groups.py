from pyramid.view import view_config

from h import (
    i18n,
    models,
    paginator,
)
from h.security import Permission

_ = i18n.TranslationString


@view_config(
    route_name="admin.groups",
    request_method="GET",
    renderer="h:templates/admin/groups.html.jinja2",
    permission=Permission.AdminPage.LOW_RISK,
)
@paginator.paginate_query
def groups_index(_context, request):
    """Retrieve a paginated list of all groups, filtered by optional group name parameter."""

    group_svc = request.find_service(name="group")
    name = request.params.get("q")

    return group_svc.filter_by_name(name)


def _userid(username, authority):  # pragma: no cover
    return models.User(username=username, authority=authority).userid

from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.i18n import TranslationString as _
from h.security import Permission


@view_config(
    route_name="admin.staff",
    request_method="GET",
    renderer="h:templates/admin/staff.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
)
def staff_index(request):
    """Get a list of all the staff members as an HTML page."""
    staff = request.db.query(models.User).filter(models.User.staff)
    return {
        "staff": [u.userid for u in staff],
        "default_authority": request.default_authority,
    }


@view_config(
    route_name="admin.staff",
    request_method="POST",
    request_param="add",
    renderer="h:templates/admin/staff.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def staff_add(request):
    """Make a given user a staff member."""
    username = request.params["add"].strip()
    authority = request.params["authority"].strip()
    user = models.User.get_by_username(request.db, username, authority)
    if user is None:
        request.session.flash(
            # pylint:disable=consider-using-f-string
            _("User {username} doesn't exist.".format(username=username)),
            "error",
        )
    else:
        user.staff = True
    index = request.route_path("admin.staff")
    return httpexceptions.HTTPSeeOther(location=index)


@view_config(
    route_name="admin.staff",
    request_method="POST",
    request_param="remove",
    renderer="h:templates/admin/staff.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def staff_remove(request):
    """Remove a user from the staff."""
    userid = request.params["remove"]
    user = request.db.query(models.User).filter_by(userid=userid).first()
    if user is not None:
        user.staff = False
    index = request.route_path("admin.staff")
    return httpexceptions.HTTPSeeOther(location=index)

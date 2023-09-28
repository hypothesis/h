from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.i18n import TranslationString as _
from h.security import Permission


class UserNotFoundError(Exception):
    pass


@view_config(
    route_name="admin.nipsa",
    request_method="GET",
    renderer="h:templates/admin/nipsa.html.jinja2",
    permission=Permission.AdminPage.HIGH_RISK,
)
def nipsa_index(request):
    nipsa_service = request.find_service(name="nipsa")
    return {
        "userids": sorted(nipsa_service.fetch_all_flagged_userids()),
        "default_authority": request.default_authority,
    }


@view_config(
    route_name="admin.nipsa",
    request_method="POST",
    request_param="add",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def nipsa_add(request):
    username = request.params["add"].strip()
    authority = request.params["authority"].strip()
    user = models.User.get_by_username(request.db, username, authority)

    if user is None:
        raise UserNotFoundError(
            # pylint:disable=consider-using-f-string
            _(
                "Could not find user with username %s and authority %s"
                % (username, authority)
            )
        )

    nipsa_service = request.find_service(name="nipsa")
    nipsa_service.flag(user)

    index = request.route_path("admin.nipsa")
    return httpexceptions.HTTPSeeOther(index)


@view_config(
    route_name="admin.nipsa",
    request_method="POST",
    request_param="remove",
    permission=Permission.AdminPage.HIGH_RISK,
    require_csrf=True,
)
def nipsa_remove(request):
    userid = request.params["remove"]
    user = request.db.query(models.User).filter_by(userid=userid).first()
    if user is None:
        # pylint:disable=consider-using-f-string
        raise UserNotFoundError(_("Could not find user with userid %s" % userid))

    nipsa_service = request.find_service(name="nipsa")
    nipsa_service.unflag(user)

    index = request.route_path("admin.nipsa")
    return httpexceptions.HTTPSeeOther(index)


@view_config(context=UserNotFoundError)
def user_not_found(exc, request):  # pragma: no cover
    request.session.flash(str(exc), "error")
    return httpexceptions.HTTPFound(location=request.route_path("admin.nipsa"))

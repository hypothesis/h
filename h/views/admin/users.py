from markupsafe import Markup
from pyramid import httpexceptions
from pyramid.view import view_config

from h import models
from h.accounts.events import ActivationEvent
from h.i18n import TranslationString as _
from h.security import Permission
from h.services.user_rename import UserRenameError


class UserNotFoundError(Exception):
    pass


def format_date(date):
    """Format a date for presentation in the UI."""

    if date is None:
        return ""

    # Format here is "2012-01-29 21:19"
    return date.strftime("%Y-%m-%d %H:%M")


@view_config(
    route_name="admin.users",
    request_method="GET",
    renderer="h:templates/admin/users.html.jinja2",
    permission=Permission.AdminPage.LOW_RISK,
)
def users_index(request):
    user = None
    user_meta = {}
    username = request.params.get("username")
    authority = request.params.get("authority")

    if username:
        username = username.strip()
        authority = authority.strip()
        user = models.User.get_by_username(request.db, username, authority)
        if user is None:
            user = models.User.get_by_email(request.db, username, authority)

    if (user is not None) and user.deleted:
        # Don't show users that're marked as deleted on admin pages.
        #
        # Users that're marked as deleted can't login or authenticate requests
        # in any way. They're in the process of being purged by a background
        # task and will soon be really deleted from the DB.
        #
        # Showing these users on admin pages is confusing because admins may
        # have already deleted a user (so the user has been marked as deleted
        # and is now going to be purged) and then think that the user has not
        # been deleted successfully because they still show up on the admin
        # pages.
        #
        # Also we don't want admins to be able to do things like rename users
        # who're marked as deleted and in the process of being purged.
        user = None

    if user is not None:
        svc = request.find_service(name="annotation_stats")
        user_meta["annotations_count"] = svc.total_user_annotation_count(user.userid)

    return {
        "default_authority": request.default_authority,
        "username": username,
        "authority": authority,
        "user": user,
        "user_meta": user_meta,
        "format_date": format_date,
    }


@view_config(
    route_name="admin.users_activate",
    request_method="POST",
    request_param="userid",
    permission=Permission.AdminPage.LOW_RISK,
    require_csrf=True,
)
def users_activate(request):
    user = _form_request_user(request)

    user.activate()

    request.session.flash(
        # pylint:disable=consider-using-f-string
        Markup(_("User {name} has been activated!".format(name=user.username))),
        "success",
    )

    request.registry.notify(ActivationEvent(request, user))

    return httpexceptions.HTTPFound(
        location=request.route_path(
            "admin.users",
            _query=(("username", user.username), ("authority", user.authority)),
        )
    )


@view_config(
    route_name="admin.users_rename",
    request_method="POST",
    permission=Permission.AdminPage.LOW_RISK,
    require_csrf=True,
)
def users_rename(request):  # pragma: no cover
    user = _form_request_user(request)

    old_username = user.username
    new_username = request.params.get("new_username").strip()

    svc = request.find_service(name="user_rename")
    try:
        svc.rename(user, new_username)

    except (UserRenameError, ValueError) as exc:
        request.session.flash(str(exc), "error")

        return httpexceptions.HTTPFound(
            location=request.route_path(
                "admin.users",
                _query=(("username", old_username), ("authority", user.authority)),
            )
        )

    request.session.flash(
        f'The user "{old_username}" will be renamed to "{new_username}" in the '
        "background. Refresh this page to see if it's already done"
        "success",
    )

    return httpexceptions.HTTPFound(
        location=request.route_path(
            "admin.users",
            _query=(("username", new_username), ("authority", user.authority)),
        )
    )


@view_config(
    route_name="admin.users_delete",
    request_method="POST",
    permission=Permission.AdminPage.LOW_RISK,
    require_csrf=True,
)
def users_delete(request):
    user = _form_request_user(request)
    svc = request.find_service(name="user_delete")

    svc.delete_user(user, requested_by=request.user, tag=request.matched_route.name)
    request.session.flash(
        f"Successfully deleted user {user.username} with authority {user.authority}"
        "success",
    )

    return httpexceptions.HTTPFound(location=request.route_path("admin.users"))


@view_config(context=UserNotFoundError)
def user_not_found(exc, request):
    request.session.flash(Markup(_(str(exc))), "error")
    return httpexceptions.HTTPFound(location=request.route_path("admin.users"))


def _form_request_user(request):
    """Return the User which a user admin form action relates to."""
    userid = request.params["userid"].strip()
    user_service = request.find_service(name="user")
    user = user_service.fetch(userid)

    if user is None:
        raise UserNotFoundError(f"Could not find user with userid {userid}")

    return user

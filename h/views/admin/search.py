from dateutil.parser import isoparse
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from h import models, tasks
from h.security import Permission


class NotFoundError(Exception):
    pass


@view_config(context=NotFoundError)
def not_found(exc, request):  # pragma: no cover
    request.session.flash(str(exc), "error")
    return HTTPFound(location=request.route_url("admin.search"))


@view_defaults(route_name="admin.search", permission=Permission.AdminPage.HIGH_RISK)
class SearchAdminViews:
    def __init__(self, request):
        self.request = request
        self.queue_service = request.find_service(name="queue_service")

    @view_config(request_method="GET", renderer="h:templates/admin/search.html.jinja2")
    def get(self):
        return {}

    @view_config(
        request_method="POST",
        request_param="reindex_date",
        require_csrf=True,
        renderer="h:templates/admin/search.html.jinja2",
    )
    def reindex_date(self):
        start_time = isoparse(self.request.params["start"].strip())
        end_time = isoparse(self.request.params["end"].strip())

        tasks.job_queue.add_annotations_between_times.delay(
            self.request.params["name"],
            start_time,
            end_time,
            tag="reindex_date",
        )
        return self._notify_reindexing_started(
            f"Began reindexing from {start_time} to {end_time}"
        )

    @view_config(
        request_method="POST",
        request_param="reindex_user",
        require_csrf=True,
        renderer="h:templates/admin/search.html.jinja2",
    )
    def reindex_user(self):
        username = self.request.params["username"].strip()
        force = bool(self.request.params.get("reindex_user_force"))

        user = models.User.get_by_username(
            self.request.db, username, self.request.default_authority
        )
        if not user:
            raise NotFoundError(f"User {username} not found")

        tasks.job_queue.add_annotations_from_user.delay(
            self.request.params["name"],
            user.userid,
            tag="reindex_user",
            force=force,
        )
        return self._notify_reindexing_started(
            f"Began reindexing annotations by {user.userid}"
        )

    @view_config(
        request_method="POST",
        request_param="reindex_group",
        require_csrf=True,
        renderer="h:templates/admin/search.html.jinja2",
    )
    def reindex_group(self):
        groupid = self.request.params["groupid"].strip()
        force = bool(self.request.params.get("reindex_group_force"))

        group = self.request.find_service(name="group").fetch_by_pubid(groupid)
        if not group:
            raise NotFoundError(f"Group {groupid} not found")

        tasks.job_queue.add_annotations_from_group.delay(
            self.request.params["name"],
            groupid,
            tag="reindex_group",
            force=force,
        )
        return self._notify_reindexing_started(
            f"Began reindexing annotations in group {groupid} ({group.name})"
        )

    def _notify_reindexing_started(self, message):
        self.request.session.flash(message, "success")
        return HTTPFound(self.request.route_url("admin.search"))

from dateutil.parser import isoparse
from pyramid.view import view_config, view_defaults

from h.tasks.indexer import reindex_annotations_in_date_range


@view_defaults(route_name="admin.search", permission="admin_search")
class SearchAdminViews:
    def __init__(self, request):
        self.request = request

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
        start_date = isoparse(self.request.params["start"].strip())
        end_date = isoparse(self.request.params["end"].strip())

        task = reindex_annotations_in_date_range.delay(start_date, end_date)
        self.request.session.flash(
            f"Began reindexing from {start_date} to {end_date}", "success"
        )

        return {"indexing": True, "task_id": task.id}

from dateutil.parser import isoparse
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults


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
        start_time = isoparse(self.request.params["start"].strip())
        end_time = isoparse(self.request.params["end"].strip())

        self.request.find_service(name="search_index").add_annotations_between_times(
            start_time, end_time, tag="reindex_date()"
        )

        self.request.session.flash(
            f"Began reindexing from {start_time} to {end_time}", "success"
        )

        return HTTPFound(self.request.route_url("admin.search"))

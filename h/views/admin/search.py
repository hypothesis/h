from dateutil.parser import isoparse
from pyramid.view import view_config, view_defaults

from h.models import Annotation


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

        annotation_ids = [
            row[0]
            for row in self.request.db.query(Annotation.id)
            .filter(Annotation.updated >= start_date)
            .filter(Annotation.updated <= end_date)
        ]

        self.request.find_service(name="job_queue").add_sync_annotation_jobs(
            annotation_ids, "reindex_date"
        )

        self.request.session.flash(
            f"Scheduled reindexing of {len(annotation_ids)} annotations", "success"
        )

        return {}

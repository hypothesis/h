import json

from pyramid.view import view_config, view_defaults

from h.schemas import ValidationError
from h.schemas.annotation import URLMigrationSchema
from h.security import Permission
from h.tasks.url_migration import move_annotations_by_url


@view_defaults(route_name="admin.documents", permission=Permission.AdminPage.HIGH_RISK)
class DocumentsAdminViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        request_method="GET", renderer="h:templates/admin/documents.html.jinja2"
    )
    def get(self):
        return {}

    @view_config(
        request_method="POST",
        request_param="update_annotation_urls",
        require_csrf=True,
        renderer="h:templates/admin/documents.html.jinja2",
    )
    def update_annotation_urls(self):
        try:
            url_mappings_json = json.loads(self.request.params["url_mappings"])
        except ValueError as err:
            return self.report_error(f"Failed to parse URL mappings: {err}")

        schema = URLMigrationSchema()

        try:
            url_mappings = schema.validate(url_mappings_json)
        except ValidationError as err:
            return self.report_error(f"Failed to validate URL mappings: {err}")

        # Chunk up the URLs into batches to limit the work per task.
        move_annotations_by_url.chunks(url_mappings.items(), 10).apply_async()

        self.request.session.flash(
            f"URL migration started for {len(url_mappings)} URL(s)", "success"
        )

        return {}

    def report_error(self, message):
        self.request.session.flash(message, "error")
        self.request.response.status_code = 400
        return {}

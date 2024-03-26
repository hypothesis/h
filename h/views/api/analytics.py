from pyramid.httpexceptions import HTTPNoContent
from pyramid.request import Request

from h.schemas.analytics import CreateEventSchema
from h.services.analytics import AnalyticsService
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.analytics.events",
    request_method="POST",
    link_name="analytics.events.create",
    description="Create a new analytics event",
)
def create_event(request: Request):
    """Create a new analytics event."""
    schema = CreateEventSchema()
    analytics_service: AnalyticsService = request.find_service(name="analytics")

    analytics_service.create(schema.validate(request.json_body))

    return HTTPNoContent()

import logging

from h.schemas.analytics import Event

log = logging.getLogger(__name__)


class AnalyticsService:
    def create(self, event: Event):
        # TODO Enhance this
        log.info(event)


def analytics_service_factory(_context, _request):
    return AnalyticsService()

import logging

log = logging.getLogger(__name__)


class AnalyticsService:
    def create(self, event_metadata: dict):
        # TODO Enhance this
        log.info(event_metadata)


def analytics_service_factory(_context, _request):
    return AnalyticsService()

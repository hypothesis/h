import logging

from h.schemas.analytics import Event


class AnalyticsService:
    def __init__(self):
        self._log = logging.getLogger(__name__)

    def create(self, event: Event):
        # TODO Enhance this
        self._log.info(event)


def analytics_service_factory(_context, _request):
    return AnalyticsService()

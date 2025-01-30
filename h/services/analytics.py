import logging

from h.schemas.analytics import Event


class AnalyticsService:
    def __init__(self):
        self._log = logging.getLogger(__name__)

    def create(self, event: Event):
        # TODO Enhance this  # noqa: FIX002, TD002, TD003, TD004
        self._log.info(event)


def analytics_service_factory(_context, _request):
    return AnalyticsService()

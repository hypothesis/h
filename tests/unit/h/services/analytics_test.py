import logging
from unittest import mock

from h.services.analytics import analytics_service_factory


class TestAnalyticsService:
    @mock.patch.object(logging, "getLogger")
    def test_it_logs_events(self, mock_get_logger):
        mock_logger = mock.Mock()
        mock_get_logger.return_value = mock_logger

        svc = analytics_service_factory({}, None)
        svc.create({"foo": "bar"})

        mock_logger.info.assert_called_once_with({"foo": "bar"})

import pytest

from h.schemas import ValidationError
from h.views.api.analytics import create_event


@pytest.mark.usefixtures("analytics_service")
class TestCreateEvent:
    def test_analytics_service_is_invoked(self, pyramid_request, analytics_service):
        pyramid_request.json_body = {"event": "client.realtime.apply_updates"}
        res = create_event(pyramid_request)

        assert analytics_service.create.called
        assert res.status_code == 204

    def test_error_if_invalid_event_payload_is_provided(
        self, pyramid_request, analytics_service
    ):
        pyramid_request.json_body = {}
        with pytest.raises(ValidationError):
            create_event(pyramid_request)

        assert not analytics_service.create.called

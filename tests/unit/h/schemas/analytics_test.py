import pytest

from h.schemas import ValidationError
from h.schemas.analytics import CreateEventSchema


class TestCreateEventSchema:
    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({}, "'event' is a required property"),
            ({"foo": "bar"}, "'event' is a required property"),
            # Deliberately not matching the full list of valid events: it grows
            # every time we add one, and spelling it out here just makes this
            # test fail for unrelated reasons.
            ({"event": "invalid"}, "event: 'invalid' is not one of"),
        ],
    )
    def test_error_for_invalid_data(self, payload: dict, expected_error: str):
        schema = CreateEventSchema()
        with pytest.raises(ValidationError, match=expected_error):
            schema.validate(payload)

    @pytest.mark.parametrize(
        "event",
        ["client.realtime.apply_updates", "client.survey.instructor_role.shown"],
    )
    def test_valid_data_is_returned(self, event: str):
        schema = CreateEventSchema()
        result = schema.validate({"event": event})

        assert result == {"event": event}

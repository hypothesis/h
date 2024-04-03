import pytest

from h.schemas import ValidationError
from h.schemas.analytics import CreateEventSchema


class TestCreateEventSchema:
    @pytest.mark.parametrize(
        "payload,expected_error",
        [
            ({}, "'event' is a required property"),
            ({"foo": "bar"}, "'event' is a required property"),
            (
                {"event": "invalid"},
                "event: 'invalid' is not one of \\['client.realtime.apply_updates'\\]",
            ),
        ],
    )
    def test_error_for_invalid_data(self, payload: dict, expected_error: str):
        schema = CreateEventSchema()
        with pytest.raises(ValidationError, match=expected_error):
            schema.validate(payload)

    def test_valid_data_is_returned(self):
        schema = CreateEventSchema()
        result = schema.validate({"event": "client.realtime.apply_updates"})

        assert result == {"event": "client.realtime.apply_updates"}

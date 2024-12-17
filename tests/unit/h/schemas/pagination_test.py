import pytest
from webob.multidict import NestedMultiDict

from h.schemas import ValidationError
from h.schemas.pagination import PaginationQueryParamsSchema
from h.schemas.util import validate_query_params


class TestPaginationQueryParamsSchema:
    @pytest.mark.parametrize(
        "input_,output",
        [
            ({}, {"page[number]": 1, "page[size]": 20}),
            (
                {"page[number]": 150, "page[size]": 50},
                {"page[number]": 150, "page[size]": 50},
            ),
        ],
    )
    def test_valid(self, schema, input_, output):
        input_ = NestedMultiDict(input_)

        assert validate_query_params(schema, input_) == output

    @pytest.mark.parametrize(
        "input_,message",
        [
            (
                {"page[number]": 0},
                r"^page\[number\]: 0 is less than minimum value 1$",
            ),
            ({"page[size]": 0}, r"^page\[size\]: 0 is less than minimum value 1$"),
            (
                {"page[size]": 101},
                r"^page\[size\]: 101 is greater than maximum value 100$",
            ),
            (
                {"page[number]": "foo", "page[size]": "bar"},
                r'^page\[number\]: "foo" is not a number\npage\[size\]: "bar" is not a number$',
            ),
        ],
    )
    def test_invalid(self, schema, input_, message):
        input_ = NestedMultiDict(input_)

        with pytest.raises(ValidationError, match=message):
            validate_query_params(schema, input_)

    @pytest.fixture
    def schema(self):
        return PaginationQueryParamsSchema()

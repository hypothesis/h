import pytest
from webob.multidict import NestedMultiDict

from h.schemas import ValidationError
from h.schemas.pagination import PaginationQueryParamsSchema
from h.schemas.util import validate_query_params


class TestPaginationQueryParamsSchema:
    @pytest.mark.parametrize(
        "input_,output",
        [
            ({}, {"page[offset]": 0, "page[limit]": 200}),
            (
                {"page[offset]": 150, "page[limit]": 50},
                {"page[offset]": 150, "page[limit]": 50},
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
                {"page[offset]": -1},
                r"^page\[offset\]: -1 is less than minimum value 0$",
            ),
            ({"page[limit]": 0}, r"^page\[limit\]: 0 is less than minimum value 1$"),
            (
                {"page[limit]": 501},
                r"^page\[limit\]: 501 is greater than maximum value 500$",
            ),
            (
                {"page[offset]": "foo", "page[limit]": "bar"},
                r'^page\[offset\]: "foo" is not a number\npage\[limit\]: "bar" is not a number$',
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

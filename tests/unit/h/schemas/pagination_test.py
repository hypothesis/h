import pytest
from webob.multidict import MultiDict, NestedMultiDict

from h.schemas import ValidationError
from h.schemas.pagination import Pagination, PaginationQueryParamsSchema
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


class TestPagination:
    @pytest.mark.parametrize(
        "params,expected",
        [
            ({"page[number]": 1, "page[size]": 20}, (0, 20)),
            ({"page[number]": 2, "page[size]": 20}, (20, 20)),
            ({"page[number]": 3, "page[size]": 10}, (20, 10)),
        ],
    )
    def test_from_params(self, params, expected):
        pagination = Pagination.from_params(MultiDict(params))

        assert pagination.offset == expected[0]
        assert pagination.limit == expected[1]

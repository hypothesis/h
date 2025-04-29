from dataclasses import dataclass

from colander import Integer, Range, Schema, SchemaNode

from h.schemas.util import validate_query_params


class PaginationQueryParamsSchema(Schema):
    page = SchemaNode(Integer(), name="page[number]", validator=Range(min=1), missing=1)
    size = SchemaNode(
        Integer(), name="page[size]", validator=Range(min=1, max=100), missing=20
    )


@dataclass
class Pagination:
    offset: int
    limit: int

    @classmethod
    def from_params(cls, params: dict) -> "Pagination":
        pagination_params = validate_query_params(PaginationQueryParamsSchema(), params)
        page_number = pagination_params["page[number]"]
        page_size = pagination_params["page[size]"]

        return cls(
            offset=page_size * (page_number - 1),
            limit=page_size,
        )

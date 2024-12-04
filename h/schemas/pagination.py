from colander import Integer, Range, Schema, SchemaNode


class PaginationQueryParamsSchema(Schema):
    offset = SchemaNode(
        Integer(),
        name="page[offset]",
        validator=Range(min=0),
        missing=0,
    )
    limit = SchemaNode(
        Integer(),
        name="page[limit]",
        validator=Range(min=1, max=100),
        missing=20,
    )

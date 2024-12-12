from colander import Integer, Range, Schema, SchemaNode


class PaginationQueryParamsSchema(Schema):
    page = SchemaNode(
        Integer(),
        name="page[number]",
        validator=Range(min=1),
        missing=1,
    )
    size = SchemaNode(
        Integer(),
        name="page[size]",
        validator=Range(min=1, max=100),
        missing=20,
    )

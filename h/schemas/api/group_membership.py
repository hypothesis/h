from h.schemas.base import JSONSchema


class EditGroupMembershipAPISchema(JSONSchema):
    schema = {
        "type": "object",
        "properties": {
            "roles": {
                "type": "array",
                "minItems": 1,
                "maxItems": 1,
                "items": {
                    "enum": ["member", "moderator", "admin", "owner"],
                },
            }
        },
        "required": ["roles"],
    }

"""Create commands for the bulk tests."""
from h.h_api.bulk_api import CommandBuilder

AUTHORITY = "lms.hypothes.is"


def _merge_query(command, authority):
    command.body.attributes.update(command.body.query)
    command.body.attributes["authority"] = authority

    return command


def UserUpsertCommand(
    number=0, authority=AUTHORITY, query_authority=AUTHORITY, **extras
):
    attributes = {
        "username": f"user_{number}",
        "display_name": f"display_name_{number}",
        "authority": query_authority,
        "identities": [{"provider": "provider", "provider_unique_id": f"pid_{number}"}],
    }

    return _merge_query(
        CommandBuilder.user.upsert(dict(attributes, **extras), f"user_ref_{number}"),
        authority,
    )


def GroupUpsertCommand(
    number=0, authority=AUTHORITY, query_authority=AUTHORITY, **extras
):
    attributes = {
        "name": f"name_{number}",
        "authority": query_authority,
        "authority_provided_id": f"ap_id_{number}",
    }

    return _merge_query(
        CommandBuilder.group.upsert(dict(attributes, **extras), f"group_ref_{number}"),
        authority,
    )

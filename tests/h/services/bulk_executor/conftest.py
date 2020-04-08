"""Create commands for the bulk tests."""
from h.h_api.bulk_api import CommandBuilder

AUTHORITY = "lms.hypothes.is"


def upsert_user_command(n=0, authority=AUTHORITY, query_authority=AUTHORITY, **extras):
    attributes = {
        "username": f"user_{n}",
        "display_name": f"display_name_{n}",
        "authority": query_authority,
        "identities": [{"provider": "provider", "provider_unique_id": f"pid_{n}"}],
    }

    command = CommandBuilder.user.upsert(dict(attributes, **extras), f"user_ref_{n}")
    command.prepare_for_execute([command], {"merge_query": True})
    command.body.attributes["authority"] = authority

    return command


def group_upsert_command(n=0, authority=AUTHORITY, query_authority=AUTHORITY, **extras):
    attributes = {
        "name": f"name_{n}",
        "authority": query_authority,
        "authority_provided_id": f"ap_id_{n}",
    }

    command = CommandBuilder.group.upsert(dict(attributes, **extras), f"group_ref_{n}")
    command.prepare_for_execute([command], {"merge_query": True})
    command.body.attributes["authority"] = authority

    return command

"""Re-usable fixtures for the bulk executor tests."""
import pytest
from h_api.bulk_api import CommandBuilder

from h.models import User

AUTHORITY = "lms.ca.hypothes.is"


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


def group_membership_create(user_id, group_id):
    command = CommandBuilder.group_membership.create("temp", "temp")

    # The builder is only really setup for creating what we need when
    # calling, which doesn't include the real ids (only references). So we
    # have to bodge it for the tests
    relationships = command.body.raw["data"]["relationships"]
    relationships["member"]["data"]["id"] = user_id
    relationships["group"]["data"]["id"] = group_id

    return command


@pytest.fixture
def user(db_session):
    user = User(_username="username", authority=AUTHORITY)
    db_session.add(user)
    db_session.flush()

    return user

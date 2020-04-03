from h.h_api.bulk_api import CommandBuilder

AUTHORITY = "lms.hypothes.is"


def make_group_command(authority=AUTHORITY, query_authority=AUTHORITY):
    command = CommandBuilder.group.upsert(
        {
            "name": "name",
            "authority": query_authority,
            "authority_provided_id": "authority_provided_id",
        },
        "id_ref",
    )

    # Fake the effect of merging in the query
    command.body.attributes["authority"] = authority

    return command


def make_user_commmand(authority=AUTHORITY, query_authority=AUTHORITY):
    command = CommandBuilder.user.upsert(
        {
            "username": "username",
            "display_name": "display_name",
            "authority": query_authority,
            "identities": [{"provider": "p", "provider_unique_id": "pid"}],
        },
        "id_ref",
    )

    # Fake the effect of merging in the query
    command.body.attributes["authority"] = authority

    return command
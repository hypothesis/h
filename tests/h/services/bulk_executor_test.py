import pytest
from pytest import param

from h.h_api.bulk_api import CommandBuilder
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.exceptions import InvalidDeclarationError
from h.services.bulk_executor import AuthorityCheckingExecutor

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


class TestAuthorityCheckingExecutor:
    def test_it_raises_InvalidDeclarationError_with_non_lms_authority(self):
        config = Configuration.create(
            effective_user="acct:user@bad_authority.com", total_instructions=2
        )

        with pytest.raises(InvalidDeclarationError):
            AuthorityCheckingExecutor().configure(config)

    @pytest.mark.parametrize(
        "command",
        (
            param(make_user_commmand(authority="bad"), id="bad user attr"),
            param(make_user_commmand(query_authority="bad"), id="bad user query"),
            param(make_group_command(authority="bad"), id="bad group attr"),
            param(make_group_command(query_authority="bad"), id="bad group query"),
        ),
    )
    def test_it_raises_InvalidDeclarationError_with_called_with_non_lms_authority(
        self, command
    ):
        with pytest.raises(InvalidDeclarationError):
            AuthorityCheckingExecutor().execute_batch(
                command.type, command.body.type, {}, [command]
            )

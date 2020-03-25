import pytest

from h.h_api.bulk_api import CommandBuilder
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.exceptions import InvalidDeclarationError
from h.services.bulk_executor import AuthorityCheckingExecutor


def make_group_command(groupid, query_groupid):
    command = CommandBuilder.group.upsert(
        {"name": "name", "groupid": query_groupid}, "id_ref"
    )

    command.body.attributes["groupid"] = groupid

    return command


class TestAuthorityCheckingExecutor:
    good_user_id = "acct:user@lms.hypothes.is"
    good_groupid = "group:name@lms.hypothes.is"
    good_authority = "lms.hypothes.is"
    good_user_attrs = {
        "username": "username",
        "display_name": "display_name",
        "authority": good_authority,
        "identities": [{"provider": "p", "provider_unique_id": "pid"}],
    }

    def test_it_raises_InvalidDeclarationError_when_configured_with_non_lms_authority(
        self,
    ):
        config = Configuration.create(
            effective_user="acct:user@bad_authority.com", total_instructions=2
        )

        with pytest.raises(InvalidDeclarationError):
            AuthorityCheckingExecutor().configure(config)

    @pytest.mark.parametrize(
        "command",
        (
            CommandBuilder.user.upsert("acct:user@bad_authority", good_user_attrs),
            CommandBuilder.user.upsert(
                good_user_id, dict(good_user_attrs, authority="bad_authority")
            ),
            make_group_command(
                groupid=good_groupid, query_groupid="group:name@bad_authority"
            ),
            make_group_command(
                groupid="group:name@bad_authority", query_groupid=good_groupid
            ),
            CommandBuilder.group_membership.create("acct:user@bad_authority", "id_ref"),
        ),
    )
    def test_it_raises_InvalidDeclarationError_with_called_with_non_lms_authority(
        self, command
    ):
        with pytest.raises(InvalidDeclarationError):
            AuthorityCheckingExecutor().execute_batch(
                command.type, command.body.type, {}, [command]
            )

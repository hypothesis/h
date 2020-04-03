import pytest
from pytest import param


from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.exceptions import InvalidDeclarationError
from h.services.bulk_executor._executor import AuthorityCheckingExecutor
from tests.h.services.bulk_executor.conftest import make_user_commmand, \
    make_group_command


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
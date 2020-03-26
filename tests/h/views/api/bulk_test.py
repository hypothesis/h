from io import BytesIO
from unittest.mock import create_autospec

import pytest
from h_matchers import Any
from pytest import param
from webob import Response

from h.h_api.bulk_api import CommandBuilder
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.exceptions import InvalidDeclarationError, SchemaValidationError
from h.views.api.bulk import AuthorityCheckingExecutor, bulk

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


class TestBulk:
    def test_it_calls_bulk_api_correctly(self, pyramid_request, BulkAPI):
        bulk(pyramid_request)

        BulkAPI.from_byte_stream.assert_called_once_with(
            pyramid_request.body_file,
            executor=Any.instance_of(AuthorityCheckingExecutor),
        )

    def test_it_formats_responses_correctly(self, pyramid_request, return_lines):
        result = bulk(pyramid_request)

        assert isinstance(result, Response)
        assert result.status == "200 OK"
        assert result.content_type == "application/x-ndjson"
        assert result.body == b"".join(return_lines)

    @pytest.mark.usefixtures("no_return_content")
    def test_it_returns_204_if_no_content_is_to_be_returned(
        self, pyramid_request, return_lines
    ):
        result = bulk(pyramid_request)

        assert result.status == "204 No Content"

    def test_it_raises_with_output_and_invalid_input(self, BulkAPI, pyramid_request):
        def bad_generator(*_, **__):
            raise SchemaValidationError([], "Bad!")
            # Looks like this doesn't do anything, but it turns this into a
            # generator. Unless the first item is retrieved the above is not
            # executed.
            yield "good!"

        BulkAPI.from_byte_stream.side_effect = bad_generator

        with pytest.raises(SchemaValidationError):
            bulk(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.body_file = create_autospec(BytesIO)

        return pyramid_request

    @pytest.fixture
    def return_lines(self):
        return [b"line_1\n", b"line_2\n"]

    @pytest.fixture(autouse=True)
    def BulkAPI(self, patch, return_lines):
        BulkAPI = patch("h.views.api.bulk.FakeBulkAPI")
        BulkAPI.from_byte_stream.return_value = (line for line in return_lines)

        return BulkAPI

    @pytest.fixture
    def no_return_content(self, BulkAPI):
        BulkAPI.from_byte_stream.return_value = None

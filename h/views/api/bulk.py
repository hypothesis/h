from itertools import chain
from logging import getLogger

from pyramid.response import Response

from h.h_api.bulk_api import BulkAPI
from h.h_api.bulk_api.executor import AutomaticReportExecutor
from h.h_api.enums import DataType
from h.h_api.exceptions import InvalidDeclarationError
from h.views.api.config import api_config

LOG = getLogger(__name__)


class FakeBulkAPI(BulkAPI):
    """Temporary stub for return values.

    When this work is complete, BulkAPI will return values for us. But right
    now it doesn't and we need something to prove we can build a return value.
    """

    return_content = True

    @classmethod
    def from_byte_stream(cls, byte_stream, executor, observer=None):
        super().from_byte_stream(byte_stream, executor, observer=None)

        if cls.return_content:
            yield b'["Line 1"]\n'
            yield b'["Line 2"]\n'
        else:
            return None


class AuthorityCheckingExecutor(AutomaticReportExecutor):
    """A bulk executor which checks the authority."""

    def __init__(self, authority="lms.hypothes.is"):
        self.effective_user = None
        self.authority = authority

    def configure(self, config):
        self._assert_authority("effective user", config.effective_user, embedded=True)

        self.effective_user = config.effective_user

    def execute_batch(self, command_type, data_type, default_config, batch):
        for command in batch:
            self._check_authority(data_type, command.body)

        return super().execute_batch(command_type, data_type, default_config, batch)

    def _assert_authority(self, field, value, embedded=False):
        if embedded and value.endswith(f"@{self.authority}"):
            return

        if value == self.authority:
            return

        raise InvalidDeclarationError(
            f"The {field} '{value}' does not match the expected authority"
        )

    def _check_authority(self, data_type, body):
        if data_type in (DataType.USER, DataType.GROUP):
            self._assert_authority("authority", body.attributes["authority"])
            self._assert_authority("query authority", body.query["authority"])


@api_config(
    versions=["v1", "v2"],
    route_name="api.bulk",
    request_method="POST",
    link_name="bulk",
    description="Perform multiple operations in one call",
    subtype="x-ndjson",
    permission="bulk_action",
)
def bulk(request):
    """
    Perform a bulk request which can modify multiple records in on go.

    This end-point can:

     * Upsert users
     * Upsert groups
     * Add users to groups

    This end-point is intended to be called using the classes provided by
    `h.h_api.bulk_api`.
    """

    results = FakeBulkAPI.from_byte_stream(
        request.body_file, executor=AuthorityCheckingExecutor()
    )

    # No return view is required
    if results is None:
        return Response(status=204)

    # An NDJSON response is required
    if results:
        # When we get an iterator we must force the first return value to be
        # created to be sure input validation has occurred. Otherwise we might
        # raise errors outside of the view
        results = chain([next(results)], results)

        return Response(
            app_iter=results, status=200, content_type="application/x-ndjson"
        )

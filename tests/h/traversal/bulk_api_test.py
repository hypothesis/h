import pytest

from h.traversal.bulk_api import BulkAPIRoot


class TestBulkAPIRoot:
    @pytest.mark.parametrize(
        "user,principal,permission_expected",
        (
            (None, None, False),
            ("acct:user@hypothes.is", "client_authority:hypothes.is", False),
            ("acct:user@lms.hypothes.is", "client_authority:lms.hypothes.is", True),
        ),
    )
    def test_it_sets_bulk_action_permission_as_expected(
        self, set_permissions, pyramid_request, user, principal, permission_expected
    ):
        set_permissions(user, principals=[principal])

        context = BulkAPIRoot(pyramid_request)

        assert (
            pyramid_request.has_permission("bulk_action", context)
            == permission_expected
        )

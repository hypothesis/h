from unittest.mock import sentinel

import pytest

from h.traversal.bulk_api import BulkAPIRoot


class TestBulkAPIRoot:
    def test_acl_for_bulk_api(self, client_authority, ACL):
        acl = BulkAPIRoot(sentinel.request).__acl__()

        client_authority.assert_called_once_with(sentinel.request)
        ACL.for_bulk_api.assert_called_once_with(
            client_authority=client_authority.return_value
        )
        assert acl == ACL.for_bulk_api.return_value

    @pytest.fixture
    def client_authority(self, patch):
        return patch("h.traversal.bulk_api.client_authority")

    @pytest.fixture
    def ACL(self, patch):
        return patch("h.traversal.bulk_api.ACL")

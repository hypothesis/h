from unittest.mock import sentinel

import pytest

from h.traversal.root import Root


class TestRoot:
    def test_acl_matching_user(self, ACL):
        acl = Root(sentinel.request).__acl__()

        ACL.for_admin_pages.assert_called_once_with()
        assert acl == ACL.for_admin_pages.return_value

    @pytest.fixture
    def ACL(self, patch):
        return patch("h.traversal.root.ACL")

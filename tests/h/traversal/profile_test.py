from unittest.mock import sentinel

import pytest

from h.traversal.profile import ProfileRoot


class TestProfileRoot:
    def test_acl_for_profile(self, ACL):
        acl = ProfileRoot(sentinel.request).__acl__()

        ACL.for_profile.assert_called_once_with()
        assert acl == ACL.for_profile.return_value

    @pytest.fixture
    def ACL(self, patch):
        return patch("h.traversal.profile.ACL")

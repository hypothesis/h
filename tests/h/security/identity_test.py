from unittest.mock import patch

import pytest
from pyramid.interfaces import IAuthenticationPolicy

from h.security import get_identity


class TestGetIdentity:
    def test_it(self, pyramid_request):
        identity = get_identity(pyramid_request)

        pyramid_request.registry.queryUtility.assert_called_once_with(
            IAuthenticationPolicy
        )
        policy = pyramid_request.registry.queryUtility.return_value
        policy.identity.assert_called_once_with(pyramid_request)
        assert identity == policy.identity.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        with patch.object(pyramid_request.registry, "queryUtility"):
            yield pyramid_request

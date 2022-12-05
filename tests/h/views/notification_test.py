from unittest.mock import sentinel

import pytest
from pyramid.exceptions import HTTPNotFound

from h.services.subscription import InvalidUnsubscribeToken
from h.views.notification import unsubscribe


class TestUnsubscribe:
    def test_it(self, pyramid_request, subscription_service):
        pyramid_request.matchdict = {"token": sentinel.valid_token}

        result = unsubscribe(pyramid_request)

        subscription_service.unsubscribe_using_token.assert_called_once_with(
            token=sentinel.valid_token
        )
        assert not result

    def test_it_with_invalid_token(self, pyramid_request, subscription_service):
        pyramid_request.matchdict = {"token": sentinel.invalid_token}
        subscription_service.unsubscribe_using_token.side_effect = (
            InvalidUnsubscribeToken
        )

        with pytest.raises(HTTPNotFound):
            unsubscribe(pyramid_request)

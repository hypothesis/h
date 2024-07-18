import pytest

from h.security.policy.helpers import is_api_request


@pytest.mark.parametrize(
    "route_name,expected_result",
    [
        ("anything", False),
        ("api.anything", True),
    ],
)
def test_is_api_request(pyramid_request, route_name, expected_result):
    pyramid_request.matched_route.name = route_name

    assert is_api_request(pyramid_request) == expected_result


def test_is_api_request_when_matched_route_is_None(pyramid_request):
    pyramid_request.matched_route = None

    assert is_api_request(pyramid_request) is False

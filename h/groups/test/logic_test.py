import mock

from h.groups import logic


@mock.patch('h.groups.logic.hashids')
def test_url_for_group_encodes_groupid(hashids):
    """It should encode the groupid to get the hashid.

    And then pass the hashid to route_url().

    """
    hashids.encode.return_value = mock.sentinel.hashid
    request = mock.Mock()
    group = mock.Mock()

    logic.url_for_group(request, group)

    assert hashids.encode.call_args[1]['number'] == group.id
    assert request.route_url.call_args[1]['hashid'] == mock.sentinel.hashid


@mock.patch('h.groups.logic.hashids')
def test_url_for_group_returns_url(_):
    """It should return the URL from request.route_url()."""
    request = mock.Mock()
    request.route_url.return_value = mock.sentinel.group_url

    url = logic.url_for_group(request, mock.Mock())

    assert url == mock.sentinel.group_url

# -*- coding: utf-8 -*-
import mock

from h.groups import logic


def test_url_for_group_gets_group_hashid():
    """It should call group.hashid(request.hashids) to get the hashid.

    And then pass the hashid to route_url().

    """
    request = mock.Mock()
    group = mock.Mock()

    logic.url_for_group(request, group)

    group.hashid.assert_called_once_with(request.hashids)
    assert request.route_url.call_args[1]['hashid'] == (
        group.hashid.return_value)


def test_url_for_group_returns_url():
    """It should return the URL from request.route_url()."""
    request = mock.Mock()
    request.route_url.return_value = mock.sentinel.group_url

    url = logic.url_for_group(request, mock.Mock())

    assert url == mock.sentinel.group_url


@mock.patch('h.groups.logic.url_for_group')
def test_as_dict(url_for_group):
    group = mock.Mock()
    group.as_dict.return_value = {'foo': 'foo', 'bar': 'bar'}
    request = mock.Mock()

    group_dict = logic.as_dict(request, group)

    assert group_dict == {
        'foo': 'foo', 'bar': 'bar',
        'url': url_for_group.return_value
    }
    url_for_group.assert_called_once_with(request, group)

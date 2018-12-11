# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock
import pytest

from h.panels.back_link import back_link


@pytest.mark.usefixtures("routes")
class TestBackLink(object):
    def test_it_sets_back_location_from_referrer(self, pyramid_request):
        pyramid_request.referrer = "https://example.com/prev-page"

        result = back_link({}, pyramid_request)

        assert result["back_location"] == "https://example.com/prev-page"

    @pytest.mark.parametrize(
        "referrer,label",
        [
            ("https://example.com/users/currentuser", "Back to your profile page"),
            (
                "https://example.com/users/currentuser?q=tag:foo",
                "Back to your profile page",
            ),
            ("https://example.com/users/otheruser", None),
            ("https://example.com/groups/abc/def", "Back to group overview page"),
            ("https://example.com/search", None),
            (None, None),
        ],
    )
    def test_it_sets_back_label(self, pyramid_request, referrer, label):
        pyramid_request.referrer = referrer

        result = back_link({}, pyramid_request)

        assert result["back_label"] == label

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = Mock(username="currentuser")
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("group_read", "/groups/{pubid}/{slug}")
        return pyramid_config

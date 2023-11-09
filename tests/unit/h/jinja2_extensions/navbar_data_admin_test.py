from unittest.mock import patch

import pytest

from h.jinja_extensions import navbar_data_admin

STAFF_TABS = ["index", "groups", "mailer", "organizations", "users"]


class TestNavbarDataAdmin:
    @pytest.mark.parametrize("permissive", (True, False))
    def test_it(self, pyramid_config, pyramid_request, permissive):
        pyramid_config.testing_securitypolicy(permissive=permissive)

        tabs = list(navbar_data_admin(pyramid_request))

        if not permissive:
            assert not tabs
            return

        assert tabs

        for tab in tabs:
            assert tab["id"]
            assert tab["title"]
            assert not tab.get("permission")

            if route := tab.get("route"):
                assert tab["url"] == f"route:{route}"

            if children := tab.get("children"):
                for child in children:
                    assert child["title"]
                    assert child["url"] == f"route:{child['route']}"

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        with patch.object(pyramid_request, "route_url") as route_url:
            route_url.side_effect = lambda route: f"route:{route}"
            yield pyramid_request

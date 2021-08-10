import pytest

from h.services.group_links import GroupLinksService, group_links_factory


@pytest.mark.usefixtures("routes")
class TestGroupLinks:
    def test_it_returns_activity_link_for_default_authority_group(
        self, pyramid_request, factories, svc
    ):
        group = factories.OpenGroup(authority=pyramid_request.default_authority)
        links = svc.get_all(group)

        assert "html" in links

    def test_it_returns_no_activity_link_for_non_default_authority_group(
        self, factories, svc
    ):
        group = factories.OpenGroup(authority="foo.com")
        links = svc.get_all(group)

        assert "html" not in links


class TestGroupLinksFactory:
    def test_group_links_factory(self, pyramid_request):
        svc = group_links_factory(None, pyramid_request)

        assert isinstance(svc, GroupLinksService)

    def test_uses_request_default_authority(self, pyramid_request):
        pyramid_request.default_authority = "bar.com"

        svc = group_links_factory(None, pyramid_request)

        assert svc._default_authority == "bar.com"  # pylint:disable=protected-access


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/groups/{pubid}")


@pytest.fixture
def svc(pyramid_request):
    return GroupLinksService(
        default_authority=pyramid_request.default_authority,
        route_url=pyramid_request.route_url,
    )

from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPMovedPermanently

from h.traversal.group import GroupContext
from h.views import groups as views


class TestGroupCreateEditController:
    def test_create(self, pyramid_request):
        controller = views.GroupCreateEditController(sentinel.context, pyramid_request)

        result = controller.create()

        assert result == {
            "page_title": "Create a new private group",
            "mode": "create",
            "group": {
                "pubid": "",
                "name": "",
                "description": "",
                "link": "",
            },
        }

    @pytest.mark.usefixtures("routes")
    def test_edit(self, factories, pyramid_request):
        group = factories.Group()
        context = GroupContext(group)
        controller = views.GroupCreateEditController(context, pyramid_request)

        result = controller.edit()

        assert result == {
            "page_title": "Edit group details",
            "mode": "edit",
            "group": {
                "pubid": group.pubid,
                "name": group.name,
                "description": group.description,
                "link": pyramid_request.route_url(
                    "group_read", pubid=group.pubid, slug=group.slug
                ),
            },
        }


@pytest.mark.usefixtures("routes")
def test_read_noslug_redirects(pyramid_request, factories):
    group = factories.Group()

    with pytest.raises(HTTPMovedPermanently) as exc:
        views.read_noslug(GroupContext(group), pyramid_request)

    assert exc.value.location == f"/g/{group.pubid}/{group.slug}"


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/g/{pubid}/{slug}")

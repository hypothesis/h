from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPMovedPermanently

from h.assets import Environment
from h.traversal.group import GroupContext
from h.views import groups as views


@pytest.mark.usefixtures("annotation_stats_service")
class TestGroupCreateEditController:
    @pytest.mark.parametrize("group_type_flag", [True, False])
    def test_create(self, pyramid_request, assets_env, mocker, group_type_flag):
        pyramid_request.feature.flags["group_type"] = group_type_flag

        mocker.spy(views, "get_csrf_token")

        controller = views.GroupCreateEditController(sentinel.context, pyramid_request)

        result = controller.create()

        assets_env.urls.assert_called_once_with("group_forms_css")
        views.get_csrf_token.assert_called_once_with(  # pylint:disable=no-member
            pyramid_request
        )
        assert result == {
            "page_title": (
                "Create a new group"
                if group_type_flag
                else "Create a new private group"
            ),
            "js_config": {
                "styles": assets_env.urls.return_value,
                "api": {
                    "createGroup": {
                        "method": "POST",
                        "url": pyramid_request.route_url("api.groups"),
                        "headers": {
                            "X-CSRF-Token": views.get_csrf_token.spy_return  # pylint:disable=no-member
                        },
                    }
                },
                "context": {"group": None},
                "features": {
                    "group_type": group_type_flag,
                    "group_members": pyramid_request.feature.flags["group_members"],
                },
            },
        }

    @pytest.mark.usefixtures("routes")
    def test_edit(
        self, factories, pyramid_request, assets_env, mocker, annotation_stats_service
    ):
        mocker.spy(views, "get_csrf_token")
        group = factories.Group()
        context = GroupContext(group)
        controller = views.GroupCreateEditController(context, pyramid_request)

        result = controller.edit()

        assets_env.urls.assert_called_once_with("group_forms_css")
        views.get_csrf_token.assert_called_once_with(  # pylint:disable=no-member
            pyramid_request
        )
        annotation_stats_service.total_group_annotation_count.assert_called_once_with(
            group.pubid, unshared=False
        )
        assert result == {
            "page_title": "Edit group",
            "js_config": {
                "styles": assets_env.urls.return_value,
                "api": {
                    "createGroup": {
                        "method": "POST",
                        "url": pyramid_request.route_url("api.groups"),
                        "headers": {
                            "X-CSRF-Token": views.get_csrf_token.spy_return  # pylint:disable=no-member
                        },
                    },
                    "updateGroup": {
                        "method": "PATCH",
                        "url": pyramid_request.route_url("api.group", id=group.pubid),
                        "headers": {
                            "X-CSRF-Token": views.get_csrf_token.spy_return  # pylint:disable=no-member
                        },
                    },
                },
                "context": {
                    "group": {
                        "pubid": group.pubid,
                        "name": group.name,
                        "description": group.description,
                        "type": group.type,
                        "link": pyramid_request.route_url(
                            "group_read", pubid=group.pubid, slug=group.slug
                        ),
                        "num_annotations": annotation_stats_service.total_group_annotation_count.return_value,
                    }
                },
                "features": {
                    "group_type": pyramid_request.feature.flags["group_type"],
                    "group_members": pyramid_request.feature.flags["group_members"],
                },
            },
        }

    @pytest.fixture
    def assets_env(self):
        return create_autospec(Environment, instance=True, spec_set=True)

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, assets_env):
        pyramid_config.registry["assets_env"] = assets_env
        return pyramid_config

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.feature.flags["group_type"] = True
        pyramid_request.feature.flags["group_members"] = True
        return pyramid_request


@pytest.mark.usefixtures("routes")
def test_read_noslug_redirects(pyramid_request, factories):
    group = factories.Group()

    with pytest.raises(HTTPMovedPermanently) as exc:
        views.read_noslug(GroupContext(group), pyramid_request)

    assert exc.value.location == f"/g/{group.pubid}/{group.slug}"


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/g/{pubid}/{slug}")
    pyramid_config.add_route("api.group", "/api/group/{id}")
    pyramid_config.add_route("api.groups", "/api/groups")

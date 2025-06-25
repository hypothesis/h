from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPMovedPermanently

from h.assets import Environment
from h.traversal.group import GroupContext
from h.views import groups as views


@pytest.mark.usefixtures("annotation_stats_service")
class TestGroupCreateEditController:
    @pytest.mark.parametrize("flag", [True, False])
    def test_create(self, pyramid_request, assets_env, mocker, flag):
        pyramid_request.feature.flags["group_type"] = flag
        pyramid_request.feature.flags["group_moderation"] = flag
        pyramid_request.feature.flags["pre_moderation"] = flag

        mocker.spy(views, "get_csrf_token")

        controller = views.GroupCreateEditController(sentinel.context, pyramid_request)

        result = controller.create()

        assets_env.urls.assert_called_once_with("forms_css")
        views.get_csrf_token.assert_called_once_with(pyramid_request)
        assert result == {
            "page_title": (
                "Create a new group" if flag else "Create a new private group"
            ),
            "js_config": {
                "styles": assets_env.urls.return_value,
                "api": {
                    "createGroup": {
                        "method": "POST",
                        "url": pyramid_request.route_url("api.groups"),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    }
                },
                "context": {
                    "group": None,
                    "user": {"userid": sentinel.authenticated_userid},
                },
                "features": {
                    "group_type": flag,
                    "group_members": pyramid_request.feature.flags["group_members"],
                    "group_moderation": flag,
                    "pre_moderation": flag,
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

        assets_env.urls.assert_called_once_with("forms_css")
        views.get_csrf_token.assert_called_once_with(pyramid_request)
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
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    },
                    "readGroupMembers": {
                        "method": "GET",
                        "url": pyramid_request.route_url(
                            "api.group_members", pubid=group.pubid
                        ),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    },
                    "editGroupMember": {
                        "method": "PATCH",
                        "url": pyramid_request.route_url(
                            "api.group_member", pubid=group.pubid, userid=":userid"
                        ),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    },
                    "removeGroupMember": {
                        "method": "DELETE",
                        "url": pyramid_request.route_url(
                            "api.group_member", pubid=group.pubid, userid=":userid"
                        ),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    },
                    "updateGroup": {
                        "method": "PATCH",
                        "url": pyramid_request.route_url("api.group", id=group.pubid),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    },
                    "groupAnnotations": {
                        "method": "GET",
                        "url": pyramid_request.route_url(
                            "api.group_annotations", pubid=group.pubid
                        ),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
                    },
                    "annotationModeration": {
                        "method": "PATCH",
                        "url": pyramid_request.route_url(
                            "api.annotation_moderation", id=":annotationId"
                        ),
                        "headers": {"X-CSRF-Token": views.get_csrf_token.spy_return},
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
                        "pre_moderated": group.pre_moderated,
                    },
                    "user": {"userid": sentinel.authenticated_userid},
                },
                "features": {
                    "group_type": pyramid_request.feature.flags["group_type"],
                    "group_members": pyramid_request.feature.flags["group_members"],
                    "group_moderation": pyramid_request.feature.flags[
                        "group_moderation"
                    ],
                    "pre_moderation": pyramid_request.feature.flags["pre_moderation"],
                },
            },
        }

    @pytest.fixture
    def assets_env(self):
        return create_autospec(Environment, instance=True, spec_set=True)

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config, assets_env):
        pyramid_config.registry["assets_env"] = assets_env
        pyramid_config.testing_securitypolicy(sentinel.authenticated_userid)
        return pyramid_config

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.feature.flags["group_type"] = True
        pyramid_request.feature.flags["group_members"] = True
        pyramid_request.feature.flags["group_moderation"] = True
        pyramid_request.feature.flags["pre_moderation"] = True
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
    pyramid_config.add_route("api.group_members", "/api/groups/{pubid}/members")
    pyramid_config.add_route("api.group_annotations", "/api/groups/{pubid}/annotations")
    pyramid_config.add_route("api.group_member", "/api/groups/{pubid}/members/{userid}")
    pyramid_config.add_route("api.groups", "/api/groups")
    pyramid_config.add_route(
        "api.annotation_moderation", "/api/annotations/{id}/moderation"
    )

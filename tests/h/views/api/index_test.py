# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import testing
from pyramid.config import Configurator

from h.views.api import index as views


class TestIndex(object):
    def test_it_returns_the_right_links_for_annotation_endpoints(
        self, pyramid_config, pyramid_request
    ):

        # Scan `h.views.api_annotations` for API link metadata specified in @api_config
        # declarations.
        config = Configurator()
        config.scan("h.views.api.annotations")
        pyramid_request.registry.api_links = config.registry.api_links

        pyramid_config.add_route("api.search", "/dummy/search")
        pyramid_config.add_route("api.annotations", "/dummy/annotations")
        pyramid_config.add_route("api.annotation", "/dummy/annotations/:id")
        pyramid_config.add_route("api.links", "/dummy/links")

        result = views.index(testing.DummyResource(), pyramid_request)

        host = "http://example.com"  # Pyramid's default host URL'
        links = result["links"]
        assert links["annotation"]["create"]["method"] == "POST"
        assert links["annotation"]["create"]["url"] == (host + "/dummy/annotations")
        assert links["annotation"]["delete"]["method"] == "DELETE"
        assert links["annotation"]["delete"]["url"] == (host + "/dummy/annotations/:id")
        assert links["annotation"]["read"]["method"] == "GET"
        assert links["annotation"]["read"]["url"] == (host + "/dummy/annotations/:id")
        assert links["annotation"]["update"]["method"] == "PATCH"
        assert links["annotation"]["update"]["url"] == (host + "/dummy/annotations/:id")
        assert links["search"]["method"] == "GET"
        assert links["search"]["url"] == host + "/dummy/search"

        # Make sure no extra links we didn't test for
        assert set(links["annotation"].keys()) == set(
            ["create", "read", "delete", "update"]
        )
        assert set(links.keys()) == set(["annotation", "search"])

    def test_it_returns_the_right_links_for_flag_endpoints(
        self, pyramid_config, pyramid_request
    ):

        config = Configurator()
        config.scan("h.views.api.flags")
        pyramid_request.registry.api_links = config.registry.api_links
        host = "http://example.com"  # Pyramid's default host URL'

        pyramid_config.add_route("api.annotation_flag", "/dummy/annotations/:id/flag")

        result = views.index(testing.DummyResource(), pyramid_request)

        links = result["links"]

        assert links["annotation"]["flag"]["method"] == "PUT"
        assert links["annotation"]["flag"]["url"] == (
            host + "/dummy/annotations/:id/flag"
        )

    def test_it_returns_the_right_links_for_group_endpoints(
        self, pyramid_config, pyramid_request
    ):

        config = Configurator()
        config.scan("h.views.api.groups")
        pyramid_request.registry.api_links = config.registry.api_links
        host = "http://example.com"  # Pyramid's default host URL'

        pyramid_config.add_route("api.groups", "/dummy/groups")
        pyramid_config.add_route("api.group", "/dummy/groups/:id")
        pyramid_config.add_route(
            "api.group_upsert", "/dummy/groups/:id", request_method="PUT"
        )
        pyramid_config.add_route(
            "api.group_member", "/dummy/groups/:pubid/members/:userid"
        )

        result = views.index(testing.DummyResource(), pyramid_request)

        links = result["links"]
        # Groups collections
        assert links["groups"]["read"]["method"] == "GET"
        assert links["groups"]["read"]["url"] == (host + "/dummy/groups")

        # Group resources
        assert links["group"]["create"]["method"] == "POST"
        assert links["group"]["create"]["url"] == (host + "/dummy/groups")
        assert links["group"]["read"]["method"] == "GET"
        assert links["group"]["read"]["url"] == (host + "/dummy/groups/:id")
        assert links["group"]["update"]["method"] == "PATCH"
        assert links["group"]["update"]["url"] == (host + "/dummy/groups/:id")
        assert links["group"]["create_or_update"]["method"] == "PUT"
        assert links["group"]["create_or_update"]["url"] == (host + "/dummy/groups/:id")

        # Group membership
        assert links["group"]["member"]["add"]["method"] == "POST"
        assert links["group"]["member"]["add"]["url"] == (
            host + "/dummy/groups/:pubid/members/:userid"
        )
        assert links["group"]["member"]["delete"]["method"] == "DELETE"
        assert links["group"]["member"]["delete"]["url"] == (
            host + "/dummy/groups/:pubid/members/:userid"
        )

        # Make sure no extra links we didn't test for
        assert set(links["group"].keys()) == set(
            ["member", "create", "read", "create_or_update", "update"]
        )
        assert set(links["group"]["member"].keys()) == set(["add", "delete"])

    def test_it_returns_the_right_links_for_links_endpoints(
        self, pyramid_config, pyramid_request
    ):

        config = Configurator()
        config.scan("h.views.api.links")
        pyramid_request.registry.api_links = config.registry.api_links
        host = "http://example.com"  # Pyramid's default host URL'

        pyramid_config.add_route("api.links", "/dummy/links")

        result = views.index(testing.DummyResource(), pyramid_request)

        links = result["links"]

        assert links["links"]["method"] == "GET"
        assert links["links"]["url"] == (host + "/dummy/links")

    def test_it_returns_the_right_links_for_moderation_endpoints(
        self, pyramid_config, pyramid_request
    ):

        config = Configurator()
        config.scan("h.views.api.moderation")
        pyramid_request.registry.api_links = config.registry.api_links
        host = "http://example.com"  # Pyramid's default host URL'

        pyramid_config.add_route("api.annotation_hide", "/dummy/annotations/:id/hide")

        result = views.index(testing.DummyResource(), pyramid_request)

        links = result["links"]

        assert links["annotation"]["hide"]["method"] == "PUT"
        assert links["annotation"]["hide"]["url"] == (
            host + "/dummy/annotations/:id/hide"
        )
        assert links["annotation"]["unhide"]["method"] == "DELETE"
        assert links["annotation"]["unhide"]["url"] == (
            host + "/dummy/annotations/:id/hide"
        )

        assert set(links["annotation"].keys()) == set(["hide", "unhide"])

    def test_it_returns_the_right_links_for_profile_endpoints(
        self, pyramid_config, pyramid_request
    ):

        config = Configurator()
        config.scan("h.views.api.profile")
        pyramid_request.registry.api_links = config.registry.api_links
        host = "http://example.com"  # Pyramid's default host URL'

        pyramid_config.add_route("api.profile", "/dummy/profile")
        pyramid_config.add_route("api.profile_groups", "/dummy/profile/groups")

        result = views.index(testing.DummyResource(), pyramid_request)

        links = result["links"]

        assert links["profile"]["read"]["method"] == "GET"
        assert links["profile"]["read"]["url"] == (host + "/dummy/profile")
        assert links["profile"]["update"]["method"] == "PATCH"
        assert links["profile"]["update"]["url"] == (host + "/dummy/profile")

        assert links["profile"]["groups"]["read"]["method"] == "GET"
        assert links["profile"]["groups"]["read"]["url"] == (
            host + "/dummy/profile/groups"
        )

        assert set(links["profile"].keys()) == set(["read", "update", "groups"])
        assert set(links["profile"]["groups"].keys()) == set(["read"])

    def test_it_returns_the_right_links_for_user_endpoints(
        self, pyramid_config, pyramid_request
    ):

        config = Configurator()
        config.scan("h.views.api.users")
        pyramid_request.registry.api_links = config.registry.api_links
        host = "http://example.com"  # Pyramid's default host URL'

        pyramid_config.add_route("api.users", "/dummy/users")
        pyramid_config.add_route("api.user", "/dummy/users/:username")

        result = views.index(testing.DummyResource(), pyramid_request)

        links = result["links"]

        assert links["user"]["create"]["method"] == "POST"
        assert links["user"]["create"]["url"] == (host + "/dummy/users")
        assert links["user"]["update"]["method"] == "PATCH"
        assert links["user"]["update"]["url"] == (host + "/dummy/users/:username")

        assert set(links["user"].keys()) == set(["create", "update"])

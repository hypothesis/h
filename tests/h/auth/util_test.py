import pytest

from h.auth import util


class TestClientAuthority:
    @pytest.mark.parametrize(
        "principals",
        [
            ["foo", "bar", "baz"],
            ["authority", "foo"],
            [],
            ["client_authority:"],
            [" client_authority:biz.biz", "foo"],
            ["client_authority :biz.biz", "foo"],
        ],
    )
    def test_it_returns_None_if_no_client_authority_principal_match(
        self, principals, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy("LYZADOODLE", groupids=principals)

        assert util.client_authority(pyramid_request) is None

    @pytest.mark.parametrize(
        "principals,authority",
        [
            (
                ["foo", "bar", "baz", "client_authority:felicitous.com"],
                "felicitous.com",
            ),
            (["client_authority:somebody.likes.me", "foo"], "somebody.likes.me"),
        ],
    )
    def test_it_returns_authority_if_authority_principal_matchpyramid_requesi(
        self, principals, authority, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy("LYZADOODLE", groupids=principals)

        assert util.client_authority(pyramid_request) == authority


class TestAuthDomain:
    def test_it_returns_the_request_domain_if_authority_isnt_set(self, pyramid_request):
        # Make sure h.authority isn't set.
        pyramid_request.registry.settings.pop("h.authority", None)

        assert util.default_authority(pyramid_request) == pyramid_request.domain

    def test_it_allows_overriding_request_domain(self, pyramid_request):
        pyramid_request.registry.settings["h.authority"] = "foo.org"
        assert util.default_authority(pyramid_request) == "foo.org"

    def test_it_returns_str(self, pyramid_request):
        pyramid_request.domain = str(pyramid_request.domain)
        assert isinstance(util.default_authority(pyramid_request), str)

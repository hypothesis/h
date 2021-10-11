from h.security.request_methods import default_authority


class TestDefaultAuthority:
    def test_it(self, pyramid_request):
        pyramid_request.registry.settings["h.authority"] = "foo.org"
        assert default_authority(pyramid_request) == "foo.org"

    def test_it_returns_the_request_domain_if_authority_isnt_set(self, pyramid_request):
        pyramid_request.registry.settings.pop("h.authority", None)

        assert default_authority(pyramid_request) == pyramid_request.domain

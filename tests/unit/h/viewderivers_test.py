import pytest

from h.viewderivers import csp_protected_view


class TestCSPProtectedView:
    def test_noop_by_default(self, pyramid_request, derive_view):
        view = derive_view(_dummy_view)

        response = view(None, pyramid_request)

        assert "Content-Security-Policy" not in response.headers

    def test_policy(self, pyramid_request, derive_view):
        pyramid_request.registry.settings.update(
            {"csp.enabled": True, "csp": {"script-src": ["'self'"]}}
        )
        view = derive_view(_dummy_view)

        response = view(None, pyramid_request)

        assert response.headers["Content-Security-Policy"] == "script-src 'self'"

    def test_policy_complex(self, pyramid_request, derive_view):
        pyramid_request.registry.settings.update(
            {
                "csp.enabled": True,
                "csp": {
                    "font-src": ["'self'", "fonts.gstatic.com"],
                    "report-uri": ["localhost"],
                    "script-src": ["'self'"],
                    "style-src": ["'self'", "fonts.googleapis.com"],
                },
            }
        )
        view = derive_view(_dummy_view)

        response = view(None, pyramid_request)

        expected = (
            "font-src 'self' fonts.gstatic.com; "
            "report-uri localhost; "
            "script-src 'self'; "
            "style-src 'self' fonts.googleapis.com"
        )
        assert response.headers["Content-Security-Policy"] == expected

    def test_report_only(self, pyramid_request, derive_view):
        pyramid_request.registry.settings.update(
            {
                "csp.enabled": True,
                "csp.report_only": True,
                "csp": {"script-src": ["'self'"]},
            }
        )
        view = derive_view(_dummy_view)

        response = view(None, pyramid_request)

        assert (
            response.headers["Content-Security-Policy-Report-Only"]
            == "script-src 'self'"
        )
        assert "Content-Security-Policy" not in response.headers

    def test_optout(self, pyramid_request, derive_view):
        """Views should be able to opt out using the ``csp_insecure_optout`` view option."""
        pyramid_request.registry.settings.update(
            {"csp.enabled": True, "csp": {"script-src": ["'self'"]}}
        )
        view = derive_view(_dummy_view, csp_insecure_optout=True)

        response = view(None, pyramid_request)

        assert "Content-Security-Policy" not in response.headers

    @pytest.fixture
    def derive_view(self, pyramid_config):
        def _impl(view, **kwargs):
            pyramid_config.add_view_deriver(csp_protected_view)
            pyramid_config.add_route("testview", "/test")
            pyramid_config.add_view(view, route_name="testview", **kwargs)
            introspector = pyramid_config.registry.introspector

            view_ = introspector.get_category("views")[0]
            return view_["introspectable"]["derived_callable"]

        return _impl


def _dummy_view(request):
    return request.response

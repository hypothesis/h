from h.views.admin import index


class TestIndex:
    def test_release_info(self, pyramid_request):
        result = index.index(pyramid_request)

        assert "release_info" in result
        assert "hostname" in result["release_info"]
        assert "python_version" in result["release_info"]
        assert "version" in result["release_info"]

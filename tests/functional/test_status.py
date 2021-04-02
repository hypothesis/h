class TestStatus:
    def test_it(self, app):
        response = app.get("/_status")

        assert response.content_type == "application/json"
        assert response.json == {"status": "okay"}
        assert (
            response.headers["Cache-Control"]
            == "max-age=0, must-revalidate, no-cache, no-store"
        )

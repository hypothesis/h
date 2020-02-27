from h.h_api.model.json_api import JSONAPIError, JSONAPIErrorBody


class TestJSONAPIErrorBody:
    def test_plain_create(self):
        meta = {"metadata": 1}
        body = JSONAPIErrorBody.create(
            KeyError("message"),
            title="title",
            detail="detail",
            pointer="_pointer",
            status=200,
            meta=meta,
        )

        assert isinstance(body, JSONAPIErrorBody)
        assert body.raw == {
            "code": "KeyError",
            "title": "title",
            "detail": "detail",
            "meta": meta,
            "source": {"pointer": "_pointer"},
            "status": "200",
        }

        assert body.detail == "detail"

    def test_degenerate_create(self):
        body = JSONAPIErrorBody.create(KeyError("message"))

        assert body.raw == {"code": "KeyError", "title": "message"}

        assert body.detail is None


class TestJSONAPIError:
    def test_create(self):
        body = JSONAPIErrorBody.create(KeyError("message"))
        error = JSONAPIError.create([body, body])

        assert isinstance(error, JSONAPIError)

        assert error.raw == {"errors": [body.raw, body.raw]}

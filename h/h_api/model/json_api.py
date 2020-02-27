"""Generic model objects representing objects in JSON API style."""

from h.h_api.model.base import Model


class JSONAPIError(Model):
    """A JSON API error wrapper."""

    @classmethod
    def create(cls, error_bodies):
        return cls({"errors": [cls.extract_raw(body) for body in error_bodies]})


class JSONAPIErrorBody(Model):
    """A JSON API error body."""

    @classmethod
    def create(
        cls, exception, title=None, detail=None, pointer=None, status=None, meta=None
    ):
        return cls(
            cls.dict_from_populated(
                code=exception.__class__.__name__,
                title=title or exception.args[0],
                detail=detail,
                meta=meta,
                status=str(int(status)) if status is not None else None,
                source={"pointer": pointer} if pointer else None,
            )
        )

    @property
    def detail(self):
        return self.raw.get("detail", None)

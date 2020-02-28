"""Generic model objects representing objects in JSON API style."""

from h.h_api.enums import DataType
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


class JSONAPIData(Model):
    """A single JSON API data object (call or response)."""

    # TODO! - This would be nice but introduces a circular dependency with
    # Schema as it needs the error stuff above via SchemaValdiationError
    # schema = Schema.get_validator('json_api.json#/$defs/resourceObject')

    @classmethod
    def create(
        cls, data_type, _id=None, attributes=None, meta=None, relationships=None
    ):
        return cls(
            {
                "data": cls.dict_from_populated(
                    type=DataType(data_type).value,
                    id=_id,
                    attributes=attributes,
                    meta=meta,
                    relationships=relationships,
                )
            }
        )

    @property
    def _data(self):
        return self.raw["data"]

    @property
    def id(self):
        return self._data["id"]

    @property
    def type(self):
        """
        The data type of this object
        :rtype: DataType
        """
        return DataType(self._data["type"])

    @property
    def attributes(self):
        """A dict of attributes for this object."""
        return self._data["attributes"]

    @attributes.setter
    def attributes(self, attributes):
        self._data["attributes"] = attributes

    @property
    def meta(self):
        """The data metadata (not the root metadata)."""
        return self._data.get("meta", {})

    @property
    def relationships(self):
        """Relationships between this object and others"""
        return self._data["relationships"]

    @property
    def id_reference(self):
        """An id reference.

        This is a custom extension to JSON API."""
        return self.meta.get("$anchor")

"""Classes for loading and parsing JSON schema."""

from functools import lru_cache

from jsonschema import Draft7Validator, RefResolver
from pkg_resources import resource_filename

from h.h_api.exceptions import SchemaValidationError


class Validator(Draft7Validator):
    """A JSON schema validator."""

    def validate_all(self, instance, error_title="The data does not match the schema"):
        """Report all validation errors in the instance against this schema.

        :param instance: The instance to check
        :param error_title: Custom error message when errors are found
        :return: None
        :raise SchemaValidationError: When errors are found
        """

        errors = []

        for error in self.iter_errors(instance):
            errors.append(error)

        if errors:
            raise SchemaValidationError(errors, title=error_title)


class Schema:
    """JSON Schema loader."""

    BASE_DIR = resource_filename("h", "h_api/resources/schema/")
    LOCAL_RESOLVER = RefResolver(base_uri="file://" + BASE_DIR, referrer=None)

    @classmethod
    def get_schema(cls, relative_path):
        """
        Load a schema object as a plain dict

        :param relative_path: Path to the schema object
        :return: A dict representing the schema
        """

        _, schema = cls.LOCAL_RESOLVER.resolve(relative_path)

        return schema

    @classmethod
    @lru_cache(32)
    def get_validator(cls, relative_path):
        """Get a validator for the provided schema.

        The schema is relative to the `resources/schema` directory.
        You can include extra url fragments on the end of the URL:

            my_schema.json#/$defs/myObject

        :param relative_path: Path to the schema object
        """
        return Validator({"$ref": relative_path}, resolver=cls.LOCAL_RESOLVER)

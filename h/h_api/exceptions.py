from h.h_api.model.json_api import JSONAPIError, JSONAPIErrorBody


class JSONAPIException(Exception):
    """An exception which can turn itself into a a JSON API error response."""

    http_status = None

    def _error_bodies(self):
        """Get the instances of JSONAPIErrorBody representing this error."""
        raise NotImplementedError()

    def as_dict(self):
        """Get a JSON API compatible dict representing this error."""
        return JSONAPIError.create(self._error_bodies()).raw


class SchemaValidationError(JSONAPIException):
    """Represent a number of schema validation errors.

    This class can be used to build up the errors and then check if the
    exception should be raised.
    """

    http_status = 400

    def __init__(self, errors, title=None):
        """
        :param errors: List of jsonschema.exceptions.ValidationError` errors
        :param title: Custom title for the exception
        """
        if title is None:
            title = "The provided data does not match the schema"

        super().__init__(title)
        self.error_bodies = [self._format_error(error) for error in errors]

    def _format_error(self, error):
        return JSONAPIErrorBody.create(
            self,
            detail=error.message,
            pointer=self._path_to_string(error.path),
            meta={
                "schema": {"pointer": self._path_to_string(error.schema_path)},
                "context": [context.message for context in error.context],
            },
            status=self.http_status,
        )

    def _error_bodies(self):
        return self.error_bodies

    @staticmethod
    def _path_to_string(path):
        """Convert a `deque` path from jsonschema to a string."""
        return "/".join(str(item) for item in path)

    def __str__(self):
        details = (f"\n\t * {body.detail}" for body in self.error_bodies)

        return self.args[0] + ":" + "".join(details)

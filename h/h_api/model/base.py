class Model:
    """Represents an object backed by a plain data structure.

    For compatibility with JSON serialisation it's important that the inner
    data structure not contain anything which cannot be serialised. This is
    the responsibility of the implementer.
    """

    # An optional schema to apply to the contents when set
    validator = None

    # Custom message to add to any validation errors
    validation_error_title = None

    def __init__(self, raw, validate=True):
        """
        :param raw: The raw data to add to this object
        """
        self.raw = raw

        if validate and raw is not None:
            self.validate()

    def validate(self, error_title=None):
        """
        Validate the contents of this object against the schema (if any)

        If `validation_error_title` is set, then this will be used as a default
        `error_title`.

        :param error_title: A custom error message when errors are found
        :raise SchemaValidationError: When errors are found
        """
        if error_title is None:
            error_title = self.validation_error_title

        if self.validator is not None:
            self.validator.validate_all(self.raw, error_title)

    @classmethod
    def extract_raw(cls, item):
        """Get raw data from a model, or return item if it is not a Model."""
        if isinstance(item, Model):
            return item.raw

        return item

    @classmethod
    def dict_from_populated(cls, **kwargs):
        """Get a dict where keys only appear if the values are not None.

        This is quite convenient for a lot of models."""
        return {key: value for key, value in kwargs.items() if value is not None}

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.raw}>"

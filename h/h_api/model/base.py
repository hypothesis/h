class Model:
    """An object backed by a plain data structure.

    For compatibility with JSON serialisation it's important that the inner
    data structure not contain anything which cannot be serialised. This is
    the responsibility of the implementer.
    """

    def __init__(self, raw):
        """
        :param raw: The raw data to add to this object
        """
        self.raw = raw

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

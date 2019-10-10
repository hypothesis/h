"""All exceptions defined for h_pyramid_sentry."""


class FilterNotCallableError(ValueError):
    """
    An exception which indicates we were passed a non-callable object as a
    filter.
    """

    def __init__(self, _filter):
        self.filter = _filter

        super().__init__(f"Filter function is not callable: {type(_filter)}")

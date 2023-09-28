"""Custom Colander validators."""

import colander


class Email(colander.Email):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        if "msg" not in kwargs:
            kwargs["msg"] = "Invalid email address."
        super().__init__(*args, **kwargs)


class Length(colander.Length):  # pragma: no cover
    def __init__(self, *args, **kwargs):
        if "min_err" not in kwargs:
            kwargs["min_err"] = "Must be ${min} characters or more."
        if "max_err" not in kwargs:
            kwargs["max_err"] = "Must be ${max} characters or less."
        super().__init__(*args, **kwargs)

# -*- coding: utf-8 -*-
"""Custom Colander validators."""

from __future__ import unicode_literals

import colander


class Email(colander.Email):
    def __init__(self, *args, **kwargs):
        if "msg" not in kwargs:
            kwargs["msg"] = "Invalid email address."
        super(Email, self).__init__(*args, **kwargs)


class Length(colander.Length):
    def __init__(self, *args, **kwargs):
        if "min_err" not in kwargs:
            kwargs["min_err"] = "Must be ${min} characters or more."
        if "max_err" not in kwargs:
            kwargs["max_err"] = "Must be ${max} characters or less."
        super(Length, self).__init__(*args, **kwargs)

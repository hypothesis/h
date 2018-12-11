# -*- coding: utf-8 -*-
"""Custom Colander validators."""

from __future__ import unicode_literals

import colander


# Regex for email addresses.
#
# Taken from Chromium and derived from the WhatWG HTML spec
# (4.10.7.1.5 E-Mail state).
#
# This was chosen because it is a widely used and relatively simple pattern.
# Unlike `colander.Email` it supports International Domain Names (IDNs) in
# Punycode form.
HTML5_EMAIL_REGEX = (
    "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@" "[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$"
)


class Email(colander.Regex):
    """
    Validator for email addresses.

    This is a replacement for `colander.Email` which rejects certain valid email
    addresses (see https://github.com/hypothesis/h/issues/4662).
    """

    def __init__(self, msg="Invalid email address."):
        super(Email, self).__init__(HTML5_EMAIL_REGEX, msg=msg)


class Length(colander.Length):
    def __init__(self, *args, **kwargs):
        if "min_err" not in kwargs:
            kwargs["min_err"] = "Must be ${min} characters or more."
        if "max_err" not in kwargs:
            kwargs["max_err"] = "Must be ${max} characters or less."
        super(Length, self).__init__(*args, **kwargs)

# -*- coding: utf-8 -*-
"""Helpers for the Python 2 to Python 3 transition."""
import sys

__all__ = ("text_type", "string_types")

PY2 = sys.version_info[0] == 2

if not PY2:
    text_type = str
    string_types = (str,)
    unichr = chr
else:
    text_type = unicode  # noqa
    string_types = (str, unicode)  # noqa
    unichr = unichr

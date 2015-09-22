# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""


class Error(Exception):

    """Base exception class for all exceptions raised by this module."""

    pass


class Annotation(object):

    """A validator for annotations."""

    def validate(self, data):
        """Raise h.api.validation.Error if the data is invalid."""
        if 'document' in data and 'link' in data['document']:
            if not isinstance(data['document']['link'], list):
                raise Error("document.link must be an array")

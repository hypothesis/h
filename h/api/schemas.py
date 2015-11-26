# -*- coding: utf-8 -*-
"""Classes for validating data passed to the annotations API."""


class ValidationError(Exception):

    """Base exception class for all exceptions raised by this module."""

    pass


class Annotation(object):

    """A validator for annotations."""

    def validate(self, data):
        """Raise ValidationError if the data is invalid."""
        if 'document' in data and 'link' in data['document']:
            if not isinstance(data['document']['link'], list):
                raise ValidationError("document.link must be an array")

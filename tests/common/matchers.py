"""
Objects that match other objects for testing.

Implements some matching objects in the style of h_matchers library for
comparing with other objects in tests.
"""

from h_matchers.matcher.core import Matcher
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther


class Redirect302To(Matcher):
    """Matches any HTTPFound redirect to the given URL."""

    def __init__(self, location):
        super().__init__(
            f"* any redirect to: {location} *",
            lambda other: isinstance(other, HTTPFound) and other.location == location,
        )


class Redirect303To(Matcher):
    """Matches any HTTPSeeOther redirect to the given URL."""

    def __init__(self, location):
        super().__init__(
            f"* any redirect to: {location} *",
            lambda other: isinstance(other, HTTPSeeOther)
            and other.location == location,
        )

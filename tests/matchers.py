"""
Matchers for use in test assertions.

This module contains objects which can be used to write better test assertions.
Each matcher class defines an __eq__ method, allowing instances of these
matchers to be used in comparisons wherever you would usually pass a plain
value.

For example imagine you want to assert that a view returns an HTTP 302 redirect
to example.com. Without matchers you would have to do something like this:

    result = my_view()

    assert isinstance(result, HTTPFound)
    assert result.location == "https://example.com"

By using the `Redirect302To` matcher you can simply write:

    assert result == Redirect302To("https://example.com")

As a bonus, matchers will tend to print more useful debugging info when
assertions fail.

"""

from pyramid import httpexceptions

from h.models.helpers import repr_


class Matcher:
    """Base class for matcher classes below."""

    repr_attrs = ()

    def __eq__(self, other):
        msg = "subclasses should provide an __eq__ method"
        raise NotImplementedError(msg)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return repr_(self, self.repr_attrs)


class Redirect302To(Matcher):
    """Matches any HTTPFound redirect to the given URL."""

    repr_attrs = ("location",)

    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        if not isinstance(other, httpexceptions.HTTPFound):
            return False

        return other.location == self.location

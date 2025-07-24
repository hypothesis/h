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


class InstanceOf(Matcher):
    """Matches any instance of the given class with the given attrs.

    As with Python's builtin isinstance() `class_` can be either a single class
    or a tuple of classes (in which case the matcher will match instances of
    *any* of the classes in the tuple).

    If no kwargs are given then the matcher will match instances of the given
    class(es) without checking any of the instance's attributes.
    """

    def __init__(self, class_, **kwargs):
        self.class_ = class_
        self.with_attrs = kwargs

    @property
    def repr_attrs(self):
        if self.with_attrs:
            return ("class_", "with_attrs")

        return ("class_",)

    def __eq__(self, other):
        if not isinstance(other, self.class_):
            return False

        for name, value in self.with_attrs.items():
            if not getattr(other, name) == value:
                return False

        return True


class Redirect302To(Matcher):
    """Matches any HTTPFound redirect to the given URL."""

    repr_attrs = ("location",)

    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        if not isinstance(other, httpexceptions.HTTPFound):
            return False

        return other.location == self.location

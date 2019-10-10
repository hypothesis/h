"""Classes implementing the matcher pattern for testing"""
import re


class AnyString:
    """A class that matches any string at all"""

    def __str__(self):
        return "* any string *"

    def __repr__(self):
        return f"<{self.__class__.__name__} '{str(self)}'>"

    def __eq__(self, other):
        return isinstance(other, str)


class AnyStringContaining(AnyString):
    """A class that matches any string with a certain substring"""

    def __init__(self, sub_string):
        self.sub_string = sub_string

    def __eq__(self, other):
        return super().__eq__(other) and self.sub_string in other

    def __str__(self):
        return self.sub_string


class AnyStringMatching(AnyString):
    """A class that matches any regular expression"""

    def __init__(self, pattern, flags=0):
        """
        :param pattern: The raw pattern to compile into a regular expression
        :param flags: Flags `re` e.g. `re.IGNORECASE`
        """
        self.regex = re.compile(pattern, flags)

    def __eq__(self, other):
        return super().__eq__(other) and self.regex.match(other)

    def __str__(self):
        return self.regex.pattern

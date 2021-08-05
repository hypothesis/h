from zope.interface import Attribute, Interface


class IAuthenticationToken(Interface):  # pylint:disable=inherit-non-class
    """Represent an authentication token."""

    userid = Attribute("""The userid to which this token was issued.""")

    def is_valid(self):
        """Check token validity (such as expiry date)."""

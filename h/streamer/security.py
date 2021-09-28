from pyramid.interfaces import ISecurityPolicy
from zope.interface import implementer

from h.security import BearerTokenPolicy


@implementer(ISecurityPolicy)
class AccessTokenPolicy(BearerTokenPolicy):
    """A token based policy which reads from the param `access_token`."""

    @classmethod
    def get_token_string(cls, request):
        return request.GET.get("access_token", None)

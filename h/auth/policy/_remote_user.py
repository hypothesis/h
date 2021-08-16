from pyramid import interfaces
from zope import interface

from h.auth.policy._identity_base import IdentityBasedPolicy
from h.security import Identity


@interface.implementer(interfaces.IAuthenticationPolicy)
class RemoteUserAuthenticationPolicy(IdentityBasedPolicy):
    """An authentication policy which blindly trusts a header."""

    def unauthenticated_userid(self, request):
        return request.environ.get("HTTP_X_FORWARDED_USER")

    def identity(self, request):
        user_id = self.unauthenticated_userid(request)
        if not user_id:
            return None

        user = request.find_service(name="user").fetch(user_id)
        if user is None:
            return None

        return Identity(user=user)

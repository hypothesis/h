from h.auth.policy._identity_base import IdentityBasedPolicy
from h.security import Identity


class RemoteUserPolicy(IdentityBasedPolicy):
    """An authentication policy which blindly trusts a header."""

    def identity(self, request):
        user_id = request.environ.get("HTTP_X_FORWARDED_USER")
        if not user_id:
            return None

        user = request.find_service(name="user").fetch(user_id)
        if user is None:
            return None

        return Identity(user=user)

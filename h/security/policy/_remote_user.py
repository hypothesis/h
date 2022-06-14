from h.security.identity import Identity
from h.security.policy._identity_base import IdentityBasedPolicy


class RemoteUserPolicy(IdentityBasedPolicy):
    """
    An authentication policy which blindly trusts a header.

    This is enabled by setting `h.proxy_auth` in the config as described in
    `h.security`.
    """

    def identity(self, request):
        user_id = request.environ.get("HTTP_X_FORWARDED_USER")
        if not user_id:
            return None

        user = request.find_service(name="user").fetch(user_id)
        if user is None:
            return None

        return Identity.from_models(user=user)

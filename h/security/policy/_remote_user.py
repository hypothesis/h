from h.security.identity import Identity
from h.security.permits import identity_permits
from h.security.policy.helpers import userid_from_identity


class RemoteUserPolicy:
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
        if user is None or user.deleted:
            return None

        return Identity.from_models(user=user)

    def authenticated_userid(self, request):
        return userid_from_identity(self, request)

    def permits(self, request, context, permission) -> bool:
        return identity_permits(self.identity(request), context, permission)

    def remember(self, _request, _userid, **_kwargs):
        return []

    def forget(self, _request):
        return []

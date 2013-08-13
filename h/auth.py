from annotator.auth import Authenticator
from pyramid.authentication import SessionAuthenticationPolicy

from h import models


class HybridAuthenticationPolicy(SessionAuthenticationPolicy):
    def effective_principals(self, request):
        base = super(HybridAuthenticationPolicy, self)
        effective_principals = base.effective_principals(request)

        # We don't even need to translate the request even though the store
        # uses flask since both webob and werkzeug use a dict-like object for
        # `request.headers`.
        authenticator = Authenticator(models.Consumer.get_by_key)
        user = authenticator.request_user(request)

        if user is not None:
            effective_principals.append(user)

        return effective_principals

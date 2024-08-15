from h.security.identity import Identity
from h.security.permits import identity_permits
from h.security.policy._bearer_token import BearerTokenPolicy


class StreamerPolicy:
    """The Pyramid security policy for the separate "streamer" app."""

    def __init__(self):
        self._bearer_token_policy = BearerTokenPolicy()

    def forget(self, *_args, **_kwargs):
        return []

    def identity(self, *args, **kwargs):
        return self._bearer_token_policy.identity(*args, **kwargs)

    def authenticated_userid(self, request):
        return Identity.authenticated_userid(self.identity(request))

    def remember(self, *_args, **_kwargs):
        return []

    def permits(self, request, context, permission):
        return identity_permits(self.identity(request), context, permission)

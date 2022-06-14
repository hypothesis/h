from typing import Optional

from h.security.identity import Identity
from h.security.permits import identity_permits


class IdentityBasedPolicy:
    """
    A base policy which will fill a policy based on returning an identity.

    This means you only need to implement `identity()` to get a functioning
    security policy.
    """

    # pylint: disable=unused-argument
    def identity(self, request) -> Optional[Identity]:
        """
        Get an Identity object for valid credentials.

        Sub-classes should implement this to return an Identity object when
        the request contains valid credentials.

        :param request: Pyramid request to inspect
        """
        return None

    def permits(self, request, context, permission) -> bool:
        """
        Get whether a given request has the requested permission on the context.

        :param request: Pyramid request to extract identity from
        :param context: A context object
        :param permission: The permission requested
        """
        return identity_permits(self.identity(request), context, permission)

    def authenticated_userid(self, request):
        """
        Return the userid implied by the token in the passed request, if any.

        :param request: Pyramid request to inspect
        :return: The userid authenticated for the passed request or None
        """
        if (identity := self.identity(request)) and identity.user:
            return identity.user.userid

        return None

    def remember(self, _request, _userid, **_kwargs):
        return []

    def forget(self, _request):
        return []

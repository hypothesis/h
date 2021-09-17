from typing import Optional

from h.security import Identity, identity_permits, principals_for_identity


class IdentityBasedPolicy:
    @classmethod
    def identity(cls, request) -> Optional[Identity]:  # pylint: disable=unused-argument
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

    def unauthenticated_userid(self, request):  # pylint: disable=no-self-use
        """
        Return the userid implied by the token in the passed request, if any.

        :param request: Pyramid request to inspect
        :return: The userid authenticated for the passed request or None
        """

        # We actually just do the same thing for unauthenticated user ids,
        # which is to say they have to be valid.
        return self.authenticated_userid(request)

    def effective_principals(self, request):
        """
        Return a list of principals for the request.

        If authentication is unsuccessful then the only principal returned is
        `Everyone`

        :param request: Pyramid request to check
        :returns: List of principals
        """
        return principals_for_identity(self.identity(request))

    def remember(self, _request, _userid, **_kwargs):  # pylint: disable=no-self-use
        return []

    def forget(self, _request):  # pylint: disable=no-self-use
        return []

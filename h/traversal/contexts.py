"""
"Context resource" objects for Pyramid views.

Context objects are reusable components that represent "the context of a view"
or "the subject of a view".

They can do things like wrap a model object (or multiple model objects) and,
since they have access to the ``request``  object, provide access to properties
that you need the request to compute such as permissions, or route URLs for a
wrapped model object. The view, or any code that the view calls and passes the
context object into, can then make use of these properties.

These context objects are returned by the root resources in
:py:mod:`h.traversal.roots` if the route is configured to use one of those root
factories (see the :py:mod:`h.traversal.roots` for usage).

For such a route Pyramid will conveniently pass the found context object into
the view callable as the ``context`` argument.

"""
from pyramid.security import Allow


class UserContext:
    """
    Context for user-centered views

    .. todo:: Most views still traverse using ``username`` and work directly
       with User models (:class:`h.models.User`). This context should be
       expanded as we continue to move over to a more resource-based approach.
    """

    def __init__(self, user):
        self.user = user

    def __acl__(self):
        """
        Set the "read" permission for AuthClients that have a matching authority
        to the user. This supercedes the ACL in :class:`h.models.User`.

        .. todo:: This ACL should be expanded (as needed) as more views make use of
        a context versus a model directly.
        """
        acl = []

        user_authority_principal = f"client_authority:{self.user.authority}"
        acl.append((Allow, user_authority_principal, "read"))

        return acl

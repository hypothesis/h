import sqlalchemy.exc
import sqlalchemy.orm

from h.models import AuthClient
from h.traversal.root import Root, RootFactory


class AuthClientRoot(RootFactory):
    """
    Root factory for routes whose context is an :py:class:`h.traversal.AuthClientContext`.

    FIXME: This class should return AuthClientContext objects, not AuthClient
    objects.

    """

    def __getitem__(self, client_id):
        try:
            client = self.request.db.query(AuthClient).filter_by(id=client_id).one()
        except sqlalchemy.orm.exc.NoResultFound as err:
            raise KeyError() from err
        except (
            sqlalchemy.exc.StatementError,
        ) as err:  # Happens when client_id is not a valid UUID.
            raise KeyError() from err

        # Add the default root factory to this resource's lineage so that the default
        # ACL is applied. This is needed so that permissions required by auth client
        # admin views (e.g. the "admin_oauthclients" permission) are granted to admin
        # users.
        #
        # For details on how ACLs work see the docs for Pyramid's ACLAuthorizationPolicy:
        # https://docs.pylonsproject.org/projects/pyramid/en/latest/api/authorization.html
        client.__parent__ = Root(self.request)

        return client

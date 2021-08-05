import importlib_resources

from h.models import Organization


class OrganizationService:
    """A service for manipulating organizations."""

    def __init__(self, session):
        """
        Create a new organizations service.

        :param session: the SQLAlchemy session object
        """
        self.session = session

    def create(self, name, authority, logo=None):
        """
        Create a new organization.

        An organization is a group of groups.

        :param name: the human-readable name of the organization
        :param authority: the authority to which the organization belongs
        :param logo: the logo of the organization in svg format

        :returns: the created organization
        """
        organization = Organization(name=name, authority=authority, logo=logo)
        self.session.add(organization)
        return organization

    def get_by_public_id(self, pubid):
        """
        Get an organization by public id.

        :param pubid: The public id to search for
        :return: An organization model or None if no match is found
        """
        return self.session.query(Organization).filter_by(pubid=pubid).one_or_none()

    def get_default(self, authority=None):
        """
        Get the default org with an option to create it if missing.

        :param authority: Create an org with this authority if none is found
        :return: The public organization or None.
        """

        query_extra = {"authority": authority} if authority else {}

        default_org = (
            self.session.query(Organization)
            .filter_by(pubid=Organization.DEFAULT_PUBID, **query_extra)
            .one_or_none()
        )

        if not default_org and authority:
            default_org = Organization(
                name="Hypothesis", authority=authority, pubid=Organization.DEFAULT_PUBID
            )

            default_org.logo = (
                importlib_resources.files("h") / "static/images/icons/logo.svg"
            ).read_text()

            self.session.add(default_org)

        return default_org


def organization_factory(_context, request):
    """Return a OrganizationService instance for the request."""
    return OrganizationService(session=request.db)

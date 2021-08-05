class GroupLinksService:
    """A service for providing appropriate links (URLs) for a given group object."""

    def __init__(self, default_authority, route_url):
        """
        Create a group_links service.

        :param default_authority: h's "default" authority
        :param route_url: The request's route_url method for building URLs
        """
        self._default_authority = default_authority
        self._route_url = route_url

    def get_all(self, group):
        """Return a dict of all applicable links for this group."""
        links = {}
        if group.authority == self._default_authority:
            # Only groups for the default authority should have an activity page
            # link. Note that the default authority may differ from the
            # user's authority.
            links["html"] = self._route_url(
                "group_read", pubid=group.pubid, slug=group.slug
            )
        return links


def group_links_factory(_context, request):
    """Return a GroupLinksService instance for the passed context and request."""
    return GroupLinksService(
        default_authority=request.default_authority, route_url=request.route_url
    )

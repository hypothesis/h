from webob.multidict import MultiDict

from h.search import (
    DeletedFilter,
    Limiter,
    Search,
    TopLevelAnnotationsFilter,
    UserFilter,
)


class AnnotationStatsService:
    """A service for retrieving annotation stats for users and groups."""

    def __init__(self, request):
        self.request = request

    def user_annotation_count(self, userid):
        """
        Return the count of searchable top level annotations for this user.

        If the logged in user has this userid, private annotations will be
        included in this count, otherwise they will not.
        """
        params = MultiDict({"limit": 0, "user": userid})
        return self._search(params)

    def total_user_annotation_count(self, userid):
        """
        Return the count of all annotations for this user.

        This disregards permissions, private/public, etc and returns the
        total number of annotations the user has made (including replies).
        """
        params = MultiDict({"limit": 0, "user": userid})

        search = Search(self.request)
        search.clear()
        search.append_modifier(Limiter())
        search.append_modifier(DeletedFilter())
        search.append_modifier(UserFilter())

        search_result = search.run(params)
        return search_result.total

    def group_annotation_count(self, pubid):
        """Return the count of searchable top level annotations for this group."""
        params = MultiDict({"limit": 0, "group": pubid})
        return self._search(params)

    def _search(self, params):
        search = Search(self.request)
        search.append_modifier(TopLevelAnnotationsFilter())

        search_result = search.run(params)
        return search_result.total


def annotation_stats_factory(_context, request):
    """Return an AnnotationStatsService instance for the passed context and request."""
    return AnnotationStatsService(request)

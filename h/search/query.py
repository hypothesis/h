from datetime import datetime as dt

from dateutil import tz
from dateutil.parser import parse
from elasticsearch_dsl import Q
from elasticsearch_dsl.query import SimpleQueryString

from h import storage
from h.search.util import add_default_scheme, wildcard_uri_is_valid
from h.util import uri

LIMIT_DEFAULT = 20
# Elasticsearch requires offset + limit must be <= 10,000.
LIMIT_MAX = 200
OFFSET_MAX = 9800
DEFAULT_DATE = dt(1970, 1, 1, 0, 0, 0, 0).replace(tzinfo=tz.tzutc())


def popall(multidict, key):
    """Pop and return all values of the key in multidict."""
    values = multidict.getall(key)
    if values:
        del multidict[key]
    return values


class KeyValueMatcher:
    """
    Adds any parameters as straightforward key-value matchers.

    This is intended to be run after all other matchers so that any
    remaining params not popped by any other qualifier get dealt with here.
    """

    def __call__(self, search, params):
        for key, value in params.items():
            search = search.filter("match", **{key: value})
        return search


class Limiter:
    """
    Limits the number of annotations returned by the search.

    Searchers for annotations starting at offset and ending at limit.
    """

    def __call__(self, search, params):
        starting_offset = self._extract_offset(params)
        ending_offset = starting_offset + self._extract_limit(params)
        return search[starting_offset:ending_offset]

    @staticmethod
    def _extract_offset(params):
        offset = params.pop("offset", 0)
        try:
            val = int(offset)
        except ValueError:
            return 0

        # val must be 0 <= val <= OFFSET_MAX.
        val = min(val, OFFSET_MAX)
        val = max(val, 0)
        return val

    @staticmethod
    def _extract_limit(params):
        limit = params.pop("limit", LIMIT_DEFAULT)
        try:
            val = int(limit)
        except ValueError:
            return LIMIT_DEFAULT

        # val must be 0 <= val <= LIMIT_MAX but if
        # val < 0 then set it to the default.
        val = min(val, LIMIT_MAX)
        if val < 0:
            return LIMIT_DEFAULT

        return val


class Sorter:
    """
    Sorts and returns annotations after search_after.

    Sorts annotations by sort (the key to sort by)
    and the order (the order in which to sort by).

    Returns annotations after search_after. search_after
    must be the value of the annotation's sort field.
    """

    def __call__(self, search, params):
        sort_by = params.pop("sort", "updated")
        # Sorting must be done on non-analyzed fields.
        if sort_by == "user":
            sort_by = "user_raw"

        # Since search_after depends on the field that the annotations are
        # being sorted by, it is set here rather than in a separate class.
        search_after = params.pop("search_after", None)
        if search_after:
            if sort_by in ["updated", "created"]:
                search_after = self._parse_date(search_after)

        if search_after:
            search = search.extra(search_after=[search_after])

        return search.sort(
            {
                sort_by: {
                    "order": params.pop("order", "desc"),
                    # `unmapped_type` causes unknown fields specified as arguments to
                    # `sort` behave as if all documents contained empty values of the
                    # given type. Without this, specifying eg. `sort=foobar` throws
                    # an exception.
                    #
                    # We use the field type `boolean` to assist with migration because
                    # that exists in both ES 1 and ES 6.
                    "unmapped_type": "boolean",
                }
            }
        )

    @staticmethod
    def _parse_date(str_value):
        """
        Convert a string to a float representing milliseconds since the epoch.

        Since the elasticsearch date parser is not run on search_after,
        the date must be converted to ms since the epoch as that is how
        the dates are stored in the elasticsearch index.
        """
        # Dates like "2017" can also be cast as floats so if a number is less
        # than 9999 it is assumed to be a year and not ms since the epoch.
        try:  # pylint: disable=too-many-try-statements
            epoch = float(str_value)
            if epoch < 9999:
                raise ValueError("This is not in the form ms since the epoch.")
            return epoch
        except ValueError:
            try:  # pylint: disable=too-many-try-statements
                date = parse(str_value, default=DEFAULT_DATE)
                return dt.timestamp(date) * 1000

            except ValueError:
                pass

        return None


class TopLevelAnnotationsFilter:
    """Matches top-level annotations only, filters out replies."""

    def __call__(self, search, _):
        return search.exclude("exists", field="references")


class AuthorityFilter:
    """Match annotations created by users belonging to a specific authority."""

    def __init__(self, authority):
        self.authority = authority

    def __call__(self, search, params):
        return search.filter("term", authority=self.authority)


class AuthFilter:
    """
    A filter that selects only annotations the user is authorised to see.

    Only annotations that are shared, or private annotations made
    by the logged-in user will pass through this filter.
    """

    def __init__(self, request):
        """
        Initialize a new AuthFilter.

        :param request: the pyramid.request object
        """
        self.request = request

    def __call__(self, search, params):
        userid = self.request.authenticated_userid
        if userid is None:
            return search.filter("term", shared=True)

        return search.filter(
            Q("bool", should=[Q("term", shared=True), Q("term", user_raw=userid)])
        )


class GroupFilter:
    """
    Filter that limits which groups annotations are returned from.

    This excludes annotations from groups that the user is not authorized to
    read or which are explicitly excluded by the search query.
    """

    def __init__(self, request):
        self.user = request.user
        self.group_service = request.find_service(name="group")

    def __call__(self, search, params):
        # Remove parameter if passed, preventing it being passed to default query
        group_ids = popall(params, "group") or None
        groups = self.group_service.groupids_readable_by(self.user, group_ids)
        return search.filter("terms", group=groups)


class UriCombinedWildcardFilter:
    """
    A filter that selects only annotations where the uri matches.

    If separate_keys is True:
        Wildcard searches are only performed on wildcard_uri's, and exact match searches
        are performed on uri/url parameters.
    If separate_keys is False:
        uri/url parameters are expected to contain exact matches and wildcard matches.
        Values containing wildcards are interpreted as wildcard searches.

    If specifying a uri with wildcards:
    * will match any character sequence (including an empty one), and a ? will match
    any single character.
    """

    def __init__(self, request, separate_keys=False):
        """
        Initialize a new UriFilter.

        :param request: the pyramid.request object
        :param separate_keys: if True will treat wildcard_uri as wildcards and uri/url
            as exact match. If False will treat any values in uri/url containing wildcards
            ("_" or "*") as wildcard searches.

        """
        self.request = request
        self.separate_keys = separate_keys

    def __call__(self, search, params):
        # If there are no uris to search for there is nothing to do so return early.
        if not ("uri" in params or "url" in params or "wildcard_uri" in params):
            return search

        if self.separate_keys:
            uris = [
                add_default_scheme(u)
                for u in popall(params, "uri") + popall(params, "url")
            ]
            wildcard_uris = [
                add_default_scheme(u) for u in popall(params, "wildcard_uri")
            ]
        else:
            uris = [
                add_default_scheme(u)
                for u in popall(params, "uri") + popall(params, "url")
            ]
            # Split into wildcard uris and non wildcard uris.
            wildcard_uris = [u for u in uris if "*" in u or "_" in u]
            uris = [u for u in uris if "*" not in u and "_" not in u]

        # Only add valid uri's to the search list.
        wildcard_uris = self._normalize_uris(
            [u for u in wildcard_uris if wildcard_uri_is_valid(u)],
            normalize_method=self._wildcard_uri_normalized,
        )
        uris = self._normalize_uris(uris)

        queries = []
        if wildcard_uris:
            queries = [Q("wildcard", **{"target.scope": u}) for u in wildcard_uris]
        if uris:
            queries.append(Q("terms", **{"target.scope": uris}))
        return search.query("bool", should=queries)

    def _normalize_uris(self, query_uris, normalize_method=uri.normalize):
        uris = set()
        for query_uri in query_uris:
            expanded = storage.expand_uri(self.request.db, query_uri)

            uris.update([normalize_method(uri) for uri in expanded])
        return list(uris)

    @staticmethod
    def _wildcard_uri_normalized(wildcard_uri):
        r"""
        Normalize a URL (like `uri.normalized`) replacing "_" with "?" after normalization.

        Although elasticsearch uses ? we use _ since ? is a special reserved url
        character and this means we can avoid dealing with normalization headaches.

        While it's possible to escape wildcards`using \\, the uri.normalize
        converts \\ to encoded url format which does not behave the same in
        elasticsearch. Thus, escaping wildcard characters is not currently
        supported.
        """
        # If the url is something like http://example.com/*, normalize it to
        #  http://example.com* so it finds all urls including the base url.
        trailing_wildcard = ""
        if wildcard_uri.endswith("*"):
            trailing_wildcard = wildcard_uri[-1]
            wildcard_uri = wildcard_uri[:-1]
        wildcard_uri = uri.normalize(wildcard_uri)
        wildcard_uri += trailing_wildcard
        return wildcard_uri.replace("_", "?")


class UserFilter:
    """A filter that selects only annotations where the 'user' parameter matches."""

    def __call__(self, search, params):
        if "user" not in params:
            return search

        users = [v.lower() for v in popall(params, "user")]

        return search.filter("terms", user=users)


class DeletedFilter:
    """
    A filter that only returns non-deleted documents.

    Documents are not getting deleted from the index, they only get marked as
    deleted.
    """

    def __call__(self, search, _):
        return search.exclude("exists", field="deleted")


class HiddenFilter:
    """Return an Elasticsearch filter for filtering out moderated or NIPSA'd annotations."""

    def __init__(self, request):
        self.group_service = request.find_service(name="group")
        self.user = request.user

    def __call__(self, search, _):
        """Filter out all hidden and NIPSA'd annotations except the current user's."""
        # If any one of these "should" clauses is true then the annotation will
        # get through the filter.
        should_clauses = [
            Q("bool", must_not=[Q("term", nipsa=True), Q("term", hidden=True)])
        ]

        if self.user is not None:
            # Always show the logged-in user's annotations even if they have
            # been hidden or the user has been NIPSA'd
            should_clauses.append(Q("term", user=self.user.userid.lower()))

        return search.filter(Q("bool", should=should_clauses))


class AnyMatcher:
    """Match the contents of a selection of fields against the `any` parameter."""

    def __call__(self, search, params):
        if "any" not in params:
            return search
        query = " ".join(popall(params, "any"))
        return search.query(
            SimpleQueryString(
                query=query,
                fields=["quote", "tags", "text", "uri.parts"],
                default_operator="and",
            )
        )


class TagsMatcher:
    """Match the tags field against 'tag' or 'tags' parameters."""

    def __call__(self, search, params):
        tags = set(popall(params, "tag") + popall(params, "tags"))
        matchers = [Q("match", tags={"query": t, "operator": "and"}) for t in tags]
        if matchers:
            return search.query(Q("bool", must=matchers))
        return search


class RepliesMatcher:
    """Match any replies to any of the given annotation ids."""

    def __init__(self, ids):
        self.annotation_ids = ids

    def __call__(self, search, _):
        return search.query(
            Q("bool", must=[Q("terms", references=self.annotation_ids)])
        )


class TagsAggregation:
    def __init__(self, limit=10):
        self.limit = limit
        self.name = "tags"

    def __call__(self, search, _):
        search.aggs.bucket(self.name, "terms", size=self.limit, field="tags_raw")

    def parse_result(self, result):
        return [
            {"tag": b["key"], "count": b["doc_count"]}
            for b in result[self.name]["buckets"]
        ]


class UsersAggregation:
    def __init__(self, limit=10):
        self.limit = limit
        self.name = "users"

    def __call__(self, search, _):
        search.aggs.bucket(self.name, "terms", size=self.limit, field="user_raw")

    def parse_result(self, result):
        return [
            {"user": b["key"], "count": b["doc_count"]}
            for b in result[self.name]["buckets"]
        ]

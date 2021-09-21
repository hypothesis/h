"""Activity pages views."""

from urllib.parse import urlparse

from jinja2 import Markup
from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults

from h import util
from h.activity import query
from h.i18n import TranslationString as _
from h.links import pretty_link
from h.models.group import ReadableBy
from h.paginator import paginate
from h.presenters.organization_json import OrganizationJSONPresenter
from h.search import parser
from h.security import Permission
from h.util.datetime import utc_us_style_date
from h.util.user import split_user
from h.views.groups import check_slug

PAGE_SIZE = 200


@view_defaults(
    route_name="activity.search", renderer="h:templates/activity/search.html.jinja2"
)
class SearchController:
    """View callables for the "activity.search" route."""

    def __init__(self, request):
        self.request = request
        # Cache a copy of the extracted query params for the child controllers to use if needed.
        self.parsed_query_params = query.extract(self.request)

    @view_config(request_method="GET")
    def search(self):
        # Make a copy of the query params to be consumed by search.
        query_params = self.parsed_query_params.copy()

        # Check whether a redirect is required.
        query.check_url(self.request, query_params)

        page_size = self.request.params.get("page_size", PAGE_SIZE)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = PAGE_SIZE

        # Fetch results.
        results = query.execute(self.request, query_params, page_size=page_size)

        groups_suggestions = []

        if self.request.user:
            for group in self.request.user.groups:
                groups_suggestions.append({"name": group.name, "pubid": group.pubid})

        def tag_link(tag):
            tag = parser.unparse({"tag": tag})
            return self.request.route_url("activity.search", _query=[("q", tag)])

        def username_from_id(userid):
            parts = split_user(userid)
            return parts["username"]

        def user_link(userid):
            username = username_from_id(userid)
            return self.request.route_url("activity.user_search", username=username)

        return {
            "search_results": results,
            "groups_suggestions": groups_suggestions,
            "page": paginate(self.request, results.total, page_size=page_size),
            "pretty_link": pretty_link,
            "q": self.request.params.get("q", ""),
            "tag_link": tag_link,
            "user_link": user_link,
            "username_from_id": username_from_id,
            # The message that is shown (only) if there's no search results.
            "zero_message": _("No annotations matched your search."),
        }


@view_defaults(
    route_name="group_read",
    renderer="h:templates/activity/search.html.jinja2",
    request_method="GET",
)
class GroupSearchController(SearchController):
    """View callables unique to the "group_read" route."""

    def __init__(self, context, request):
        super().__init__(request)
        self.context = context
        self.group = context.group

    @view_config(request_method="GET")
    def search(self):  # pylint: disable=too-complex
        result = self._check_access_permissions()
        if result is not None:
            return result

        check_slug(self.group, self.request)

        result = super().search()

        result["opts"] = {"search_groupname": self.group.name}

        # If the group has read access only for members  and the user is not in that list
        # return without extra info.
        if self.group.readable_by == ReadableBy.members and (
            self.request.user not in self.group.members
        ):
            return result

        def user_annotation_count(aggregation, userid):
            for user in aggregation:
                if user["user"] == userid:
                    return user["count"]
            return 0

        members = []
        moderators = []
        users_aggregation = result["search_results"].aggregations.get("users", [])
        # If the group has members provide a list of member info,
        # otherwise provide a list of moderator info instead.
        if self.group.members:
            members = [
                {
                    "username": u.username,
                    "userid": u.userid,
                    "count": user_annotation_count(users_aggregation, u.userid),
                    "faceted_by": _faceted_by_user(
                        self.request, u.username, self.parsed_query_params
                    ),
                }
                for u in self.group.members
            ]
            members = sorted(members, key=lambda k: k["username"].lower())
        else:
            moderators = []
            if self.group.creator:
                # Pass a list of moderators, anticipating that [self.group.creator]
                # will change to an actual list of moderators at some point.
                moderators = [
                    {
                        "username": u.username,
                        "userid": u.userid,
                        "count": user_annotation_count(users_aggregation, u.userid),
                        "faceted_by": _faceted_by_user(
                            self.request, u.username, self.parsed_query_params
                        ),
                    }
                    for u in [self.group.creator]
                ]
                moderators = sorted(moderators, key=lambda k: k["username"].lower())

        group_annotation_count = self._get_total_annotations_in_group(
            result, self.request
        )

        result["stats"] = {"annotation_count": group_annotation_count}
        result["group"] = {
            "created": utc_us_style_date(self.group.created),
            "description": self.group.description,
            "name": self.group.name,
            "pubid": self.group.pubid,
            "url": self.request.route_url(
                "group_read", pubid=self.group.pubid, slug=self.group.slug
            ),
            "share_subtitle": _("Share group"),
            "share_msg": _("Sharing the link lets people view this group:"),
        }
        if self.group.organization:
            result["group"]["organization"] = OrganizationJSONPresenter(
                self.group.organization, self.request
            ).asdict(summary=True)
        else:
            result["group"]["organization"] = None

        if self.group.type == "private":
            result["group"]["share_subtitle"] = _("Invite new members")
            result["group"]["share_msg"] = _(
                "Sharing the link lets people join this group:"
            )

        result["group_users_args"] = [
            _("Members"),
            moderators if self.group.type == "open" else members,
            self.group.creator.userid if self.group.creator else None,
        ]

        if self.request.has_permission(Permission.Group.EDIT, context=self.context):
            result["group_edit_url"] = self.request.route_url(
                "group_edit", pubid=self.group.pubid
            )

        result["more_info"] = "more_info" in self.request.params

        if not result.get("q"):
            result["zero_message"] = Markup(
                _("The group “{name}” has not made any annotations yet.").format(
                    name=Markup.escape(self.group.name)
                )
            )

        result["show_leave_button"] = self.request.user in self.group.members

        return result

    def _get_total_annotations_in_group(self, result, _request):
        """
        Get number of annotations in group.

        If the search result already has this number don't run a query, just re-use it.
        """
        group_annotation_count = result["search_results"].total
        if len(self.parsed_query_params) > 1:
            group_annotation_count = self.request.find_service(
                name="annotation_stats"
            ).group_annotation_count(self.group.pubid)
        return group_annotation_count

    @view_config(request_method="POST", request_param="group_join")
    def join(self):
        """
        Join the given group.

        This adds the authenticated user to the given group and redirect the
        browser to the search page.
        """
        if not self.request.has_permission(Permission.Group.JOIN, context=self.context):
            raise httpexceptions.HTTPNotFound()

        group_members_service = self.request.find_service(name="group_members")
        group_members_service.member_join(self.group, self.request.authenticated_userid)

        url = self.request.route_url(
            "group_read", pubid=self.group.pubid, slug=self.group.slug
        )
        return httpexceptions.HTTPSeeOther(location=url)

    @view_config(
        request_method="POST",
        request_param="group_leave",
        is_authenticated=True,
    )
    def leave(self):
        """
        Leave the given group.

        Remove the authenticated user from the given group and redirect the
        browser to the search page.

        """
        group_members_service = self.request.find_service(name="group_members")
        group_members_service.member_leave(
            self.group, self.request.authenticated_userid
        )

        new_params = _copy_params(self.request, self.request.POST.copy())
        del new_params["group_leave"]
        location = self.request.route_url("activity.search", _query=new_params)

        return httpexceptions.HTTPSeeOther(location=location)

    @view_config(request_param="toggle_user_facet")
    def toggle_user_facet(self):
        """
        Toggle the given user from the search facets.

        If the search is not already faceted by the userid given in the
        "toggle_user_facet" request param then redirect the browser to the same
        page but with the a facet for this user added to the search query.

        If the search is already faceted by the userid then redirect the
        browser to the same page but with this user facet removed from the
        search query.

        """
        userid = self.request.params["toggle_user_facet"]
        username = util.user.split_user(userid)["username"]

        new_params = _copy_params(self.request)

        del new_params["toggle_user_facet"]

        parsed_query = _parsed_query(self.request)
        if _faceted_by_user(self.request, username, parsed_query):
            # The search query is already faceted by the given user,
            # so remove that user facet.
            username_facets = _username_facets(self.request, parsed_query)
            username_facets.remove(username)
            del parsed_query["user"]
            for username_facet in username_facets:
                parsed_query.add("user", username_facet)
        else:
            # The search query is not yet faceted by the given user, so add a
            # facet for the user.
            parsed_query.add("user", username)

        _update_q(new_params, parsed_query)

        location = self.request.route_url(
            "group_read",
            pubid=self.group.pubid,
            slug=self.group.slug,
            _query=new_params,
        )

        return httpexceptions.HTTPSeeOther(location=location)

    @view_config(request_param="back")
    def back(self):
        return _back(self.request)

    @view_config(request_param="delete_lozenge")
    def delete_lozenge(self):
        return _delete_lozenge(self.request)

    @view_config(request_param="toggle_tag_facet")
    def toggle_tag_facet(self):
        return _toggle_tag_facet(self.request)

    def _check_access_permissions(self):
        if not self.request.has_permission(Permission.Group.READ, context=self.context):
            show_join_page = self.request.has_permission(
                Permission.Group.JOIN, self.context
            )
            if not self.request.user:
                # Show a page which will prompt the user to login to join.
                show_join_page = True

            if show_join_page:
                self.request.override_renderer = "h:templates/groups/join.html.jinja2"
                return {"group": self.group}

            raise httpexceptions.HTTPNotFound()

        return None


@view_defaults(
    route_name="activity.user_search",
    renderer="h:templates/activity/search.html.jinja2",
)
class UserSearchController(SearchController):
    """View callables unique to the "activity.user_search" route."""

    def __init__(self, context, request):
        super().__init__(request)
        self.user = context.user

    @view_config(request_method="GET")
    def search(self):
        result = super().search()

        result["opts"] = {"search_username": self.user.username}
        result["more_info"] = "more_info" in self.request.params

        def domain(user):
            if not user.uri:
                return None
            return urlparse(user.uri).netloc

        annotation_count = self._get_total_user_annotations(result, self.request)
        result["stats"] = {"annotation_count": annotation_count}

        result["user"] = {
            "name": self.user.display_name or self.user.username,
            "description": self.user.description,
            "registered_date": utc_us_style_date(self.user.registered_date),
            "location": self.user.location,
            "uri": self.user.uri,
            "domain": domain(self.user),
            "orcid": self.user.orcid,
        }

        if self.request.user == self.user:
            result["user"]["edit_url"] = self.request.route_url("account_profile")

        if not result.get("q"):
            if self.request.user == self.user:
                # Tell the template that it should show "How to get started".
                result["zero_message"] = "__SHOW_GETTING_STARTED__"
            else:
                result["zero_message"] = _(
                    f"{result['user']['name']} has not made any annotations yet."
                )

        return result

    def _get_total_user_annotations(self, result, _request):
        """
        Get number of annotations that the user has made.

        If the search result already has this number don't run a query, just re-use it.
        """
        user_annotation_count = result["search_results"].total
        if len(self.parsed_query_params) > 1:
            user_annotation_count = self.request.find_service(
                name="annotation_stats"
            ).user_annotation_count(self.user.userid)
        return user_annotation_count

    @view_config(request_param="back")
    def back(self):
        return _back(self.request)

    @view_config(request_param="delete_lozenge")
    def delete_lozenge(self):
        return _delete_lozenge(self.request)

    @view_config(request_param="toggle_tag_facet")
    def toggle_tag_facet(self):
        return _toggle_tag_facet(self.request)


def _parsed_query(request):
    """
    Return the parsed (MultiDict) query from the given request.

    Return a copy of the given search page request's search query, parsed from
    a string into a MultiDict.

    """
    return parser.parse(request.params.get("q", ""))


def _username_facets(request, parsed_query=None):
    """
    Return a list of the usernames that the search is faceted by.

    Returns a (possibly empty) list of all the usernames that the given
    search page request's search query is already faceted by.

    """
    return (parsed_query or _parsed_query(request)).getall("user")


def _tag_facets(request, parsed_query=None):
    """
    Return a list of the tags that the search is faceted by.

    Returns a (possibly empty) list of all the tags that the given
    search page request's search query is already faceted by.

    """
    return (parsed_query or _parsed_query(request)).getall("tag")


def _faceted_by_user(request, username, parsed_query=None):
    """
    Return True if the given request is already faceted by the given username.

    Return True if the given search page request's search query already
    contains a user facet for the given username, False otherwise.

    """
    return username in _username_facets(request, parsed_query)


def _faceted_by_tag(request, tag, parsed_query=None):
    """
    Return True if the given request is already faceted by the given tag.

    Return True if the given search page request's search query already
    contains a facet for the given tag, False otherwise.

    """
    return tag in _tag_facets(request, parsed_query)


def _redirect_to_user_or_group_search(request, params):
    if request.matched_route.name == "group_read":
        location = request.route_url(
            "group_read",
            pubid=request.matchdict["pubid"],
            slug=request.matchdict["slug"],
            _query=params,
        )
    elif request.matched_route.name == "activity.user_search":
        location = request.route_url(
            "activity.user_search",
            username=request.matchdict["username"],
            _query=params,
        )
    return httpexceptions.HTTPSeeOther(location=location)


def _back(request):
    """Respond to a click on the ``back`` button."""
    new_params = _copy_params(request)
    del new_params["back"]
    return _redirect_to_user_or_group_search(request, new_params)


def _delete_lozenge(request):
    """
    Redirect to the /search page, keeping the search query intact.

    When on the user or group search page a lozenge for the user or group
    is rendered as the first lozenge in the search bar. The delete button
    on that first lozenge calls this view. Redirect to the general /search
    page, effectively deleting that first user or group lozenge, but
    maintaining any other search terms that have been entered into the
    search box.

    """
    new_params = _copy_params(request)
    del new_params["delete_lozenge"]
    location = request.route_url("activity.search", _query=new_params)
    return httpexceptions.HTTPSeeOther(location=location)


def _toggle_tag_facet(request):
    """
    Toggle the given tag from the search facets.

    If the search is not already faceted by the tag given in the
    "toggle_tag_facet" request param then redirect the browser to the same
    page but with the a facet for this  added to the search query.

    If the search is already faceted by the tag then redirect the browser
    to the same page but with this facet removed from the search query.

    """
    tag = request.params["toggle_tag_facet"]

    new_params = _copy_params(request)

    del new_params["toggle_tag_facet"]

    parsed_query = _parsed_query(request)
    if _faceted_by_tag(request, tag, parsed_query):
        # The search query is already faceted by the given tag,
        # so remove that tag facet.
        tag_facets = _tag_facets(request, parsed_query)
        tag_facets.remove(tag)
        del parsed_query["tag"]
        for tag_facet in tag_facets:
            parsed_query.add("tag", tag_facet)
    else:
        # The search query is not yet faceted by the given tag, so add a facet
        # for the tag.
        parsed_query.add("tag", tag)

    _update_q(new_params, parsed_query)

    return _redirect_to_user_or_group_search(request, new_params)


def _update_q(params, parsed_query):
    """
    Update the given request params based on the given parsed_query.

    Update the value of the 'q' string in the given request params based on the
    given parsed_query.

    If the query parses to an empty string then ensure that there is no 'q' in
    the given request params, to avoid redirecting the browser to a URL with an
    empty trailing ?q=

    """
    query_ = parser.unparse(parsed_query)
    if query_.strip():
        params["q"] = query_
    else:
        params.pop("q", None)


def _copy_params(request, params=None):
    """
    Return a copy of the given request's params.

    If the request contains an empty 'q' param then it is omitted from the
    returned copy of the params, to avoid redirecting the browser to a URL with
    an empty trailing ?q=

    """
    if params is None:
        params = request.params.copy()

    if "q" in params and not params["q"].strip():
        del params["q"]

    return params

# -*- coding: utf-8 -*-

"""Activity pages views."""

from __future__ import unicode_literals

import urlparse

from jinja2 import Markup
from pyramid import httpexceptions
from pyramid.view import view_config
from pyramid.view import view_defaults
from sqlalchemy.orm import exc
from memex.search import parser

from h import models
from h.activity import query
from h.i18n import TranslationString as _
from h.links import pretty_link
from h.paginator import paginate
from h import util
from h.util.user import split_user


PAGE_SIZE = 200


@view_defaults(route_name='activity.search',
               renderer='h:templates/activity/search.html.jinja2')
class SearchController(object):
    """View callables for the "activity.search" route."""

    def __init__(self, request):
        if not request.feature('search_page'):
            raise httpexceptions.HTTPNotFound()

        self.request = request

    @view_config(request_method='GET')
    def search(self):
        q = query.extract(self.request)

        # Check whether a redirect is required.
        query.check_url(self.request, q)

        page_size = self.request.params.get('page_size', PAGE_SIZE)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = PAGE_SIZE

        # Fetch results.
        result = query.execute(self.request, q, page_size=page_size)

        groups_suggestions = []

        if self.request.authenticated_user:
            for group in self.request.authenticated_user.groups:
                groups_suggestions.append({
                    'name': group.name,
                    'pubid': group.pubid
                })

        def tag_link(tag):
            q = parser.unparse({'tag': tag})
            return self.request.route_url('activity.search', _query=[('q', q)])

        def username_from_id(userid):
            parts = split_user(userid)
            return parts['username']

        def user_link(userid):
            username = username_from_id(userid)
            return self.request.route_url('activity.user_search',
                                          username=username)

        return {
            'aggregations': result.aggregations,
            'groups_suggestions': groups_suggestions,
            'page': paginate(self.request, result.total, page_size=page_size),
            'pretty_link': pretty_link,
            'q': self.request.params.get('q', ''),
            'tag_link': tag_link,
            'timeframes': result.timeframes,
            'total': result.total,
            'user_link': user_link,
            'username_from_id': username_from_id,
            # The message that is shown (only) if there's no search results.
            'zero_message': _('No annotations matched your search.'),
        }


@view_defaults(route_name='activity.group_search',
               renderer='h:templates/activity/search.html.jinja2')
class GroupSearchController(SearchController):
    """View callables unique to the "activity.group_search" route."""

    @view_config(request_method='GET')
    def search(self):
        result = super(GroupSearchController, self).search()

        pubid = self.request.matchdict['pubid']
        result['opts'] = {'search_groupname': pubid}

        try:
            group = (self.request.db.query(models.Group)
                     .filter_by(pubid=pubid).one())
        except exc.NoResultFound:
            return result

        result['opts']['search_groupname'] = group.name

        if self.request.authenticated_user not in group.members:
            return result

        def user_annotation_count(aggregation, userid):
            for user in aggregation:
                if user['user'] == userid:
                    return user['count']
            return 0

        q = query.extract(self.request)
        users_aggregation = result.get('aggregations', {}).get('users', [])
        members = [{'username': u.username,
                    'userid': u.userid,
                    'count': user_annotation_count(users_aggregation,
                                                   u.userid),
                    'faceted_by': _faceted_by_user(self.request,
                                                   u.username,
                                                   q)}
                   for u in group.members]
        members = sorted(members, key=lambda k: k['username'].lower())

        result['group'] = {
            'created': group.created.strftime('%B, %Y'),
            'description': group.description,
            'name': group.name,
            'pubid': group.pubid,
            'url': self.request.route_url('group_read',
                                          pubid=group.pubid,
                                          slug=group.slug),
            'members': members,
        }

        if self.request.has_permission('admin', group):
            result['group_edit_url'] = self.request.route_url('group_edit',
                                                              pubid=pubid)

        result['more_info'] = 'more_info' in self.request.params

        if not result.get('q'):
            result['zero_message'] = Markup(_(
                'The group “{name}” has not made any annotations yet.').format(
                    name=Markup.escape(group.name)))

        return result

    @view_config(request_method='POST',
                 request_param='group_leave')
    def leave(self):
        """
        Leave the given group.

        Remove the authenticated user from the given group and redirect the
        browser to the search page.

        """
        pubid = self.request.POST['group_leave']

        try:
            group = (self.request.db.query(models.Group)
                     .filter_by(pubid=pubid).one())
        except exc.NoResultFound:
            raise httpexceptions.HTTPNotFound()

        groups_service = self.request.find_service(name='groups')
        groups_service.member_leave(group, self.request.authenticated_userid)

        new_params = self.request.POST.copy()
        del new_params['group_leave']
        location = self.request.route_url('activity.search', _query=new_params)

        return httpexceptions.HTTPSeeOther(location=location)

    @view_config(request_method='POST',
                 request_param='toggle_user_facet')
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
        userid = self.request.POST['toggle_user_facet']
        username = util.user.split_user(userid)['username']

        new_params = self.request.POST.copy()

        del new_params['toggle_user_facet']

        parsed_query = _parsed_query(self.request)
        if _faceted_by_user(self.request, username, parsed_query):
            # The search query is already faceted by the given user,
            # so remove that user facet.
            username_facets = _username_facets(self.request, parsed_query)
            username_facets.remove(username)
            del parsed_query['user']
            for username_facet in username_facets:
                parsed_query.add('user', username_facet)
        else:
            # The search query is not yet faceted by the given user, so add a
            # facet for the user.
            parsed_query.add('user', username)

        new_params['q'] = parser.unparse(parsed_query)

        location = self.request.route_url(
            'activity.group_search', pubid=self.request.matchdict['pubid'],
            _query=new_params)

        return httpexceptions.HTTPSeeOther(location=location)


@view_defaults(route_name='activity.user_search',
               renderer='h:templates/activity/search.html.jinja2')
class UserSearchController(SearchController):
    """View callables unique to the "activity.user_search" route."""

    def __init__(self, user, request):
        super(UserSearchController, self).__init__(request)
        self.user = user

    @view_config(request_method='GET')
    def search(self):
        result = super(UserSearchController, self).search()

        result['opts'] = {'search_username': self.user.username}
        result['more_info'] = 'more_info' in self.request.params

        def domain(user):
            if not user.uri:
                return None
            return urlparse.urlparse(user.uri).netloc

        result['user'] = {
            'name': self.user.display_name or self.user.username,
            'num_annotations': result['total'],
            'description': self.user.description,
            'registered_date': self.user.registered_date.strftime('%B, %Y'),
            'location': self.user.location,
            'uri': self.user.uri,
            'domain': domain(self.user),
            'orcid': self.user.orcid,
        }

        if self.request.authenticated_user == self.user:
            result['user']['edit_url'] = self.request.route_url(
                'account_profile')

        if not result.get('q'):
            if self.request.authenticated_user == self.user:
                # Tell the template that it should show "How to get started".
                result['zero_message'] = '__SHOW_GETTING_STARTED__'
            else:
                result['zero_message'] = _(
                    "{name} has not made any annotations yet.".format(
                        name=result['user']['name']))

        return result


@view_defaults(request_method='GET',
               renderer='h:templates/activity/search.html.jinja2')
class GroupUserSearchController(SearchController):
    """activity.group_search and activity.user_search shared views."""

    @view_config(route_name='activity.group_search',
                 request_method='POST',
                 request_param='more_info')
    @view_config(route_name='activity.user_search',
                 request_method='POST',
                 request_param='more_info')
    def more_info(self):
        """Respond to a click on the ``more_info`` button."""
        return _redirect_to_user_or_group_search(self.request,
                                                 self.request.POST)

    @view_config(route_name='activity.group_search',
                 request_method='POST',
                 request_param='back')
    @view_config(route_name='activity.user_search',
                 request_method='POST',
                 request_param='back')
    def back(self):
        """Respond to a click on the ``back`` button."""
        new_params = self.request.POST.copy()
        del new_params['back']
        return _redirect_to_user_or_group_search(self.request, new_params)

    @view_config(route_name='activity.group_search',
                 request_param='delete_lozenge')
    @view_config(route_name='activity.user_search',
                 request_param='delete_lozenge')
    def delete_lozenge(self):
        """
        Redirect to the /search page, keeping the search query intact.

        When on the user or group search page a lozenge for the user or group
        is rendered as the first lozenge in the search bar. The delete button
        on that first lozenge calls this view. Redirect to the general /search
        page, effectively deleting that first user or group lozenge, but
        maintaining any other search terms that have been entered into the
        search box.

        """
        new_params = self.request.params.copy()
        del new_params['delete_lozenge']
        location = self.request.route_url('activity.search', _query=new_params)
        return httpexceptions.HTTPSeeOther(location=location)

    @view_config(route_name='activity.group_search',
                 request_method='POST',
                 request_param='toggle_tag_facet')
    @view_config(route_name='activity.user_search',
                 request_method='POST',
                 request_param='toggle_tag_facet')
    def toggle_tag_facet(self):
        """
        Toggle the given tag from the search facets.

        If the search is not already faceted by the tag given in the
        "toggle_tag_facet" request param then redirect the browser to the same
        page but with the a facet for this  added to the search query.

        If the search is already faceted by the tag then redirect the browser
        to the same page but with this facet removed from the search query.

        """
        tag = self.request.POST['toggle_tag_facet']

        new_params = self.request.POST.copy()

        del new_params['toggle_tag_facet']

        parsed_query = _parsed_query(self.request)
        if _faceted_by_tag(self.request, tag, parsed_query):
            # The search query is already faceted by the given tag,
            # so remove that tag facet.
            tag_facets = _tag_facets(self.request, parsed_query)
            tag_facets.remove(tag)
            del parsed_query['tag']
            for tag_facet in tag_facets:
                parsed_query.add('tag', tag_facet)
        else:
            # The search query is not yet faceted by the given tag, so add a facet
            # for the tag.
            parsed_query.add('tag', tag)

        new_params['q'] = parser.unparse(parsed_query)
        return _redirect_to_user_or_group_search(self.request, new_params)


def _parsed_query(request):
    """
    Return the parsed (MultiDict) query from the given POST request.

    Return a copy of the given search page request's search query, parsed from
    a string into a MultiDict.

    """
    return parser.parse(request.POST.get('q', ''))


def _username_facets(request, parsed_query=None):
    """
    Return a list of the usernames that the search is faceted by.

    Returns a (possibly empty) list of all the usernames that the given
    search page request's search query is already faceted by.

    """
    return (parsed_query or _parsed_query(request)).getall('user')


def _tag_facets(request, parsed_query=None):
    """
    Return a list of the tags that the search is faceted by.

    Returns a (possibly empty) list of all the tags that the given
    search page request's search query is already faceted by.

    """
    return (parsed_query or _parsed_query(request)).getall('tag')


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
    if request.matched_route.name == 'activity.group_search':
        location = request.route_url('activity.group_search',
                                     pubid=request.matchdict['pubid'],
                                     _query=params)
    elif request.matched_route.name == 'activity.user_search':
        location = request.route_url('activity.user_search',
                                     username=request.matchdict['username'],
                                     _query=params)
    return httpexceptions.HTTPSeeOther(location=location)

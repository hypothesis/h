# -*- coding: utf-8 -*-

"""Activity pages views."""

from __future__ import unicode_literals

import urlparse

from pyramid import httpexceptions
from pyramid.view import view_config
from sqlalchemy.orm import exc
from memex.search import parser

from h import models
from h.activity import query
from h.links import pretty_link
from h.paginator import paginate
from h import util
from h.util.user import split_user

PAGE_SIZE = 200


@view_config(route_name='activity.search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    q = query.extract(request)

    # Check whether a redirect is required
    query.check_url(request, q)

    page_size = request.params.get('page_size', PAGE_SIZE)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = PAGE_SIZE

    # Fetch results
    result = query.execute(request, q, page_size=page_size)

    groups_suggestions = []

    if request.authenticated_user:
        for group in request.authenticated_user.groups:
            groups_suggestions.append({
                'name': group.name,
                'pubid': group.pubid
                })

    def tag_link(tag):
        q = parser.unparse({'tag': tag})
        return request.route_url('activity.search', _query=[('q', q)])

    def username_from_id(userid):
        parts = split_user(userid)
        return parts['username']

    def user_link(userid):
        username=username_from_id(userid)
        return request.route_url('activity.user_search', username=username)

    return {
        'aggregations': result.aggregations,
        'groups_suggestions': groups_suggestions,
        'page': paginate(request, result.total, page_size=page_size),
        'pretty_link': pretty_link,
        'q': request.params.get('q', ''),
        'tag_link': tag_link,
        'timeframes': result.timeframes,
        'total': result.total,
        'user_link': user_link,
        'username_from_id': username_from_id,
    }


@view_config(route_name='activity.group_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def group_search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    result = search(request)

    pubid = request.matchdict['pubid']
    result['opts'] = {'search_groupname': pubid}

    try:
        group = request.db.query(models.Group).filter_by(pubid=pubid).one()
    except exc.NoResultFound:
        return result

    result['opts']['search_groupname'] = group.name

    if request.authenticated_user not in group.members:
        return result

    def user_annotation_count(aggregation, userid):
        for user in aggregation:
            if user['user'] == userid:
                return user['count']
        return 0

    q = query.extract(request)
    users_aggregation = result.get('aggregations', {}).get('users', [])
    members = [{'username': u.username,
                'userid': u.userid,
                'count': user_annotation_count(users_aggregation, u.userid),
                'faceted_by': _faceted_by_user(request, u.username, q)}
               for u in group.members]
    members = sorted(members, key=lambda k: k['username'].lower())

    result['group'] = {
        'created': group.created.strftime('%B, %Y'),
        'description': group.description,
        'name': group.name,
        'pubid': group.pubid,
        'url': request.route_url('group_read',
                                 pubid=group.pubid,
                                 slug=group.slug),
        'members': members,
    }

    if request.has_permission('admin', group):
        result['group_edit_url'] = request.route_url('group_edit', pubid=pubid)

    result['more_info'] = 'more_info' in request.params

    return result


@view_config(route_name='activity.user_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def user_search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    username = request.matchdict['username']

    result = search(request)
    result['opts'] = {'search_username': username}

    result['more_info'] = 'more_info' in request.params

    user = request.find_service(name='user').fetch(username,
                                                   request.auth_domain)

    if not user:
        return result

    result['opts']['search_username'] = user.display_name or user.username

    def domain(user):
        if not user.uri:
            return None
        return urlparse.urlparse(user.uri).netloc

    result['user'] = {
        'name': user.display_name or user.username,
        'num_annotations': result['total'],
        'description': user.description,
        'registered_date': user.registered_date.strftime('%B, %Y'),
        'location': user.location,
        'uri': user.uri,
        'domain': domain(user),
        'orcid': user.orcid,
    }

    if request.authenticated_user == user:
        result['user']['edit_url'] = request.route_url('account_profile')

    return result


@view_config(route_name='activity.group_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='more_info')
@view_config(route_name='activity.user_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='more_info')
def search_more_info(request):
    """Respond to a click on the ``more_info`` button."""
    return _redirect_to_user_or_group_search(request, request.POST)


@view_config(route_name='activity.group_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='back')
@view_config(route_name='activity.user_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='back')
def search_back(request):
    """Respond to a click on the ``back`` button."""
    new_params = request.POST.copy()
    del new_params['back']
    return _redirect_to_user_or_group_search(request, new_params)


@view_config(route_name='activity.group_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='group_leave')
def group_leave(request):
    """
    Leave the given group.

    Remove the authenticated user from the given group and redirect the
    browser to the search page.

    """
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    pubid = request.POST['group_leave']

    try:
        group = request.db.query(models.Group).filter_by(pubid=pubid).one()
    except exc.NoResultFound:
        raise httpexceptions.HTTPNotFound()

    groups_service = request.find_service(name='groups')
    groups_service.member_leave(group, request.authenticated_userid)

    new_params = request.POST.copy()
    del new_params['group_leave']
    location = request.route_url('activity.search', _query=new_params)

    return httpexceptions.HTTPSeeOther(location=location)


@view_config(route_name='activity.group_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='delete_lozenge')
@view_config(route_name='activity.user_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='delete_lozenge')
def delete_lozenge(request):
    """
    Redirect to the /search page, keeping the search query intact.

    When on the user or group search page a lozenge for the user or group is
    rendered as the first lozenge in the search bar. The delete button on that
    first lozenge calls this view. Redirect to the general /search page,
    effectively deleting that first user or group lozenge, but maintaining any
    other search terms that have been entered into the search box.

    """
    new_params = request.params.copy()
    del new_params['delete_lozenge']
    location = request.route_url('activity.search', _query=new_params)
    return httpexceptions.HTTPSeeOther(location=location)


@view_config(route_name='activity.group_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='toggle_user_facet')
def toggle_user_facet(request):
    """
    Toggle the given user from the search facets.

    If the search is not already faceted by the userid given in the
    "toggle_user_facet" request param then redirect the browser to the same
    page but with the a facet for this user added to the search query.

    If the search is already faceted by the userid then redirect the browser
    to the same page but with this user facet removed from the search query.

    """
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    userid = request.POST['toggle_user_facet']
    username = util.user.split_user(userid)['username']

    new_params = request.POST.copy()

    del new_params['toggle_user_facet']

    parsed_query = _parsed_query(request)
    if _faceted_by_user(request, username, parsed_query):
        # The search query is already faceted by the given user,
        # so remove that user facet.
        username_facets = _username_facets(request, parsed_query)
        username_facets.remove(username)
        if username_facets:
            parsed_query['user'] = username_facets
        else:
            del parsed_query['user']
    else:
        # The search query is not yet faceted by the given user, so add a facet
        # for the user.
        parsed_query.add('user', username)

    new_params['q'] = parser.unparse(parsed_query)

    location = request.route_url('activity.group_search',
                                 pubid=request.matchdict['pubid'],
                                 _query=new_params)

    return httpexceptions.HTTPSeeOther(location=location)


@view_config(route_name='activity.group_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='toggle_tag_facet')
@view_config(route_name='activity.user_search',
             request_method='POST',
             renderer='h:templates/activity/search.html.jinja2',
             request_param='toggle_tag_facet')
def toggle_tag_facet(request):
    """
    Toggle the given tag from the search facets.

    If the search is not already faceted by the tag given in the
    "toggle_tag_facet" request param then redirect the browser to the same
    page but with the a facet for this  added to the search query.

    If the search is already faceted by the tag then redirect the browser
    to the same page but with this facet removed from the search query.

    """
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    tag = request.POST['toggle_tag_facet']

    new_params = request.POST.copy()

    del new_params['toggle_tag_facet']

    parsed_query = _parsed_query(request)
    if _faceted_by_tag(request, tag, parsed_query):
        # The search query is already faceted by the given tag,
        # so remove that tag facet.
        tag_facets = _tag_facets(request, parsed_query)
        tag_facets.remove(tag)
        del parsed_query['tag']
        for tag_facet in tag_facets:
            parsed_query.add('tag', tag_facet)
    else:
        # The search query is not yet faceted by the given tag, so add a facet
        # for the tag.
        parsed_query.add('tag', tag)

    new_params['q'] = parser.unparse(parsed_query)
    return _redirect_to_user_or_group_search(request, new_params)


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

# -*- coding: utf-8 -*-

"""Activity pages views."""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config
from sqlalchemy.orm import exc
from memex.search import parser

from h import models
from h.activity import query
from h.paginator import paginate
from h import util

PAGE_SIZE = 200


@view_config(route_name='activity.search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
@view_config(route_name='activity.user_search',
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

    for user in result.aggregations.get('users', []):
        user['username'] = util.user.split_user(user['user'])['username']
        user['userid'] = user['user']
        user['faceted_by'] = _faceted_by_user(request, user['username'], q)
        del user['user']

    return {
        'total': result.total,
        'aggregations': result.aggregations,
        'timeframes': result.timeframes,
        'page': paginate(request, result.total, page_size=page_size),
    }


@view_config(route_name='activity.group_search',
             request_method='GET',
             renderer='h:templates/activity/search.html.jinja2')
def group_search(request):
    if not request.feature('search_page'):
        raise httpexceptions.HTTPNotFound()

    result = search(request)

    pubid = request.matchdict['pubid']

    try:
        group = request.db.query(models.Group).filter_by(pubid=pubid).one()
    except exc.NoResultFound:
        return result

    if request.authenticated_user not in group.members:
        return result

    result['group'] = {
        'created': group.created.strftime('%B, %Y'),
        'description': group.description,
        'name': group.name,
        'pubid': group.pubid,
    }

    if request.has_permission('admin', group):
        result['group_edit_url'] = request.route_url('group_edit', pubid=pubid)

    return result


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

    pubid = request.params['group_leave']

    try:
        group = request.db.query(models.Group).filter_by(pubid=pubid).one()
    except exc.NoResultFound:
        raise httpexceptions.HTTPNotFound()

    groups_service = request.find_service(name='groups')
    groups_service.member_leave(group, request.authenticated_userid)

    new_params = request.POST.copy()
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

    userid = request.params['toggle_user_facet']
    username = util.user.split_user(userid)['username']

    new_params = request.params.copy()

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


def _parsed_query(request):
    """
    Return the parsed (MultiDict) query from the given request.

    Return a copy of the given search page request's search query, parsed from
    a string into a MultiDict.

    """
    return parser.parse(request.params.get('q', ''))


def _username_facets(request, parsed_query=None):
    """
    Return a list of the usernames that the search is faceted by.

    Returns a (possibly empty) list of all the usernames that the given
    search page request's search query is already faceted by.

    """
    return (parsed_query or _parsed_query(request)).getall('user')


def _faceted_by_user(request, username, parsed_query=None):
    """
    Return True if the given request is already faceted by the given username.

    Return True if the given search page request's search query already
    contains a user facet for the given username, False otherwise.

    """
    return username in _username_facets(request, parsed_query)

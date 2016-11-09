# -*- coding: utf-8 -*-

"""
Activity pages views.
"""

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid.view import view_config
from sqlalchemy.orm import exc

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

# -*- coding: utf-8 -*-

from __future__ import division

import functools
import math

PAGE_SIZE = 20


def paginate(request, total, page_size=PAGE_SIZE):
    page_max = int(math.ceil(total / page_size))
    page_max = max(1, page_max)  # There's always at least one page.

    try:
        current_page = int(request.params['page'])
    except (KeyError, ValueError):
        current_page = 1
    current_page = max(1, current_page)
    current_page = min(current_page, page_max)

    next_ = current_page + 1 if current_page < page_max else None
    prev = current_page - 1 if current_page > 1 else None

    def url_for(page):
        query = request.params.dict_of_lists()
        query['page'] = page
        return request.current_route_path(_query=query)

    return {
        'cur': current_page,
        'max': page_max,
        'next': next_,
        'prev': prev,
        'url_for': url_for,
    }


def paginate_query(wrapped=None, page_size=PAGE_SIZE):
    """
    Decorate a view function, providing basic pagination facilities.

    Wraps a view function that returns a :py:class:`sqlalchemy.orm.query.Query`
    object in order to enable basic pagination. Returns a dictionary containing
    the results for the current page and page metadata. For example, the simple
    view function

        @paginate_query
        def my_view(context, request):
            return request.db.query(User)

    will, when wrapped, return a dictionary like the following:

        {
            "results": [<user1>, <user2>, ..., <user20>],
            "total": 135,
            "page": {
                "cur": 1,
                "max": 7,
                "next": 2,
                "prev": None,
            }
        }

    You can also call :py:func:`paginate_query` as a function which returns a
    decorator, if you wish to modify the options used by the function:

        paginate = paginator.paginate_query(page_size=10)

        @paginate_query
        def my_view(...):
            ...

    N.B. The wrapped view function must accept two arguments: the request
    context and the current request. This decorator does not support view
    functions which accept only a single argument.
    """
    if wrapped is None:
        def decorator(wrap):
            return paginate_query(wrap, page_size=page_size)
        return decorator

    @functools.wraps(wrapped)
    def wrapper(context, request):
        result = wrapped(context, request)
        total = result.count()
        page = paginate(request, total, page_size)
        offset = (page['cur'] - 1) * page_size
        return {
            'results': result.offset(offset).limit(page_size).all(),
            'total': total,
            'page': page,
        }
    return wrapper

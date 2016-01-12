# -*- coding: utf-8 -*-

from __future__ import division

import functools
import math

PAGE_SIZE = 20


def paginate(wrapped=None, page_size=PAGE_SIZE):
    """
    Decorate a view function, providing basic pagination facilities.

    Wraps a view function that returns a :py:class:`sqlalchemy.orm.query.Query`
    object in order to enable basic pagination. Returns a dictionary containing
    the results for the current page and page metadata. For example, the simple
    view function

        @paginate
        def my_view(context, request):
            return User.query

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

    You can also call :py:func:`paginate` as a function which returns a
    decorator, if you wish to modify the options used by the function:

        paginate = paginator.paginate(page_size=10)

        @paginate
        def my_view(...):
            ...

    N.B. The wrapped view function must accept two arguments: the request
    context and the current request. This decorator does not support view
    functions which accept only a single argument.
    """
    if wrapped is None:
        def decorator(wrap):
            return paginate(wrap, page_size=page_size)
        return decorator

    @functools.wraps(wrapped)
    def wrapper(context, request):
        result = wrapped(context, request)
        total = result.count()
        page_max = int(math.ceil(total / page_size))
        page_max = max(1, page_max)  # there's always at least one page

        try:
            page = int(request.params['page'])
        except (KeyError, ValueError):
            page = 1
        page = max(1, page)
        page = min(page, page_max)

        offset = (page - 1) * page_size
        limit = page_size

        out = {
            'results': result.offset(offset).limit(limit).all(),
            'total': total,
            'page': {
                'cur': page,
                'max': page_max,
                'next': page + 1 if page < page_max else None,
                'prev': page - 1 if page > 1 else None,
            }
        }
        return out
    return wrapper

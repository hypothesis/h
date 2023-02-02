from unittest import mock

import pytest
from webob.multidict import NestedMultiDict

from h.paginator import paginate, paginate_query


class TestPaginate:
    def test_current_page_defaults_to_1(self, pyramid_request):
        """If there's no 'page' request param it defaults to 1."""
        pyramid_request.params = {}

        page = paginate(pyramid_request, 600, 10)

        assert page["cur"] == 1

    @pytest.mark.parametrize(
        "page_param,expected",
        [
            # If the current page is the first page.
            ("1", [1, 2, 3, 4, "...", 60]),
            # If the current page is the last page.
            ("60", [1, "...", 57, 58, 59, 60]),
            # If the current page is in the middle.
            ("30", [1, "...", 27, 28, 29, 30, 31, 32, 33, "...", 60]),
            # If the current page is near the first page.
            ("2", [1, 2, 3, 4, 5, "...", 60]),
            # If the current page is near the last page.
            ("59", [1, "...", 56, 57, 58, 59, 60]),
        ],
    )
    def test_numbers_large_result_set(self, pyramid_request, page_param, expected):
        pyramid_request.params = {"page": page_param}
        assert paginate(pyramid_request, 600, 10)["numbers"] == expected

    @pytest.mark.parametrize(
        "page_param,expected",
        [
            # If the current page is the first page.
            ("1", [1, 2, 3, 4, 5]),
            # If the current page is the last page.
            ("5", [1, 2, 3, 4, 5]),
            # If the current page is in the middle.
            ("3", [1, 2, 3, 4, 5]),
        ],
    )
    def test_numbers_small_result_set(self, pyramid_request, page_param, expected):
        pyramid_request.params = {"page": page_param}
        assert paginate(pyramid_request, 50, 10)["numbers"] == expected

    @pytest.mark.parametrize(
        "page_param,expected",
        [
            # Normally the current page just comes directly from the request's
            # 'page' param.
            ("32", 32),
            # If the 'page' param is less than 1 the current page is clipped to 1.
            ("-3", 1),
            ("0", 1),
            # If the 'page' param isn't a number the current page defaults to 1.
            ("foo", 1),
            # If the 'page' param is greater than the number of pages the current
            # page is clipped to the number of pages.
            ("100", 60),
        ],
    )
    def test_current_page(self, pyramid_request, page_param, expected):
        pyramid_request.params = {"page": page_param}

        page = paginate(
            pyramid_request,
            # With 600 items in total and 10 items per page there are 60 pages.
            600,
            10,
        )

        assert page["cur"] == expected

    @pytest.mark.parametrize(
        "total,page_size,expected",
        [
            # Normally 'max' is just total / page_size.
            (600, 10, 60),
            # Total doesn't divide evenly into page_size.
            (605, 10, 61),
            # If total is less than page size there should be one page.
            (6, 10, 1),
        ],
    )
    def test_max(self, pyramid_request, total, page_size, expected):
        assert paginate(pyramid_request, total, page_size)["max"] == expected

    @pytest.mark.parametrize(
        "page_param,expected",
        [
            # Normally 'next' is simply the current page + 1.
            ("32", 33),
            # If the current page is the last page then 'next' is None.
            ("60", None),
        ],
    )
    def test_next(self, pyramid_request, page_param, expected):
        pyramid_request.params = {"page": page_param}
        assert paginate(pyramid_request, 600, 10)["next"] == expected

    @pytest.mark.parametrize(
        "page_param,expected",
        [
            # Normally 'prev' is simply the current page - 1.
            ("32", 31),
            # If the current page is the first page then 'prev' is None.
            ("1", None),
        ],
    )
    def test_prev(self, pyramid_request, page_param, expected):
        pyramid_request.params = {"page": page_param}
        assert paginate(pyramid_request, 600, 10)["prev"] == expected

    @pytest.mark.parametrize(
        "params,expected",
        [
            # Normally url_for() just replaces the 'page' param with the requested
            # new page number.
            ([{"page": "32"}], {"page": 26}),
            # If there is no 'page' param it just adds a 'page' param for the
            # requested page.
            ([{}], {"page": 26}),
            # Existing query params (other than 'page') should be preserved.
            (
                [{"q": "user:jeremydean", "foo": "bar"}],
                {"q": ["user:jeremydean"], "foo": ["bar"], "page": 26},
            ),
            (
                [{"q": "user:jeremydean", "foo": "bar", "page": "32"}],
                {"q": ["user:jeremydean"], "foo": ["bar"], "page": 26},
            ),
            # Repeated params should be preserved.
            ([{"foo": "one"}, {"foo": "two"}], {"foo": ["one", "two"], "page": 26}),
        ],
    )
    def test_url_for(self, pyramid_request, params, expected):
        pyramid_request.params = NestedMultiDict(*params)
        pyramid_request.current_route_path = mock.Mock(spec_set=["__call__"])
        url_for = paginate(pyramid_request, 600, 10)["url_for"]

        url = url_for(page=26)  # Request the URL for page 26.

        pyramid_request.current_route_path.assert_called_once_with(_query=expected)
        assert url == pyramid_request.current_route_path.return_value


@pytest.mark.usefixtures("paginate")
class TestPaginateQuery:
    # The current page that will be returned by paginate().
    CURRENT_PAGE = 3

    # The page_size argument that will be passed to paginate_query().
    PAGE_SIZE = 10

    def test_it_calls_the_wrapped_view_callable(
        self, pyramid_request, view_callable, wrapped
    ):
        """It calls the wrapped view callable to get the SQLAlchemy query."""
        wrapped(mock.sentinel.context, pyramid_request)

        view_callable.assert_called_once_with(mock.sentinel.context, pyramid_request)

    def test_it_calls_paginate(self, paginate, pyramid_request, wrapped):
        """It calls paginate() to get the paginator template data."""
        wrapped(mock.sentinel.context, pyramid_request)

        paginate.assert_called_once_with(
            pyramid_request, mock.sentinel.total, self.PAGE_SIZE
        )

    def test_it_offsets_the_query(self, wrapped, pyramid_request, query):
        """
        It offsets the query by the correct amount.

        It offsets the query so that only the results starting from the first
        result that should be shown on the current page (as returned by
        paginate()) are fetched from the db.

        """
        wrapped(mock.sentinel.context, pyramid_request)

        # The current page is 3, and there are 10 results per page, so we
        # would expect the 20 first results (the first two pages) to be offset.
        query.offset.assert_called_once_with(20)

    def test_it_limits_the_query(self, wrapped, pyramid_request, query):
        """
        It limits the query by the correct amount.

        It limits the query so that only the results up to the last result that
        should be shown on the current page are fetched from the db.

        """
        wrapped(mock.sentinel.context, pyramid_request)

        query.limit.assert_called_once_with(self.PAGE_SIZE)

    def test_it_returns_the_query_results(self, wrapped, pyramid_request):
        results = wrapped(mock.sentinel.context, pyramid_request)["results"]

        assert results == mock.sentinel.all

    def test_it_returns_the_total(self, wrapped, pyramid_request):
        total = wrapped(mock.sentinel.context, pyramid_request)["total"]

        assert total == mock.sentinel.total

    def test_it_returns_the_paginator_template_data(
        self, wrapped, paginate, pyramid_request
    ):
        page = wrapped(mock.sentinel.context, pyramid_request)["page"]

        assert page == paginate.return_value

    @pytest.fixture
    def paginate(self, patch):
        return patch("h.paginator.paginate", return_value={"cur": self.CURRENT_PAGE})

    @pytest.fixture
    def query(self):
        """Return a mock SQLAlchemy Query object."""
        mock_query = mock.Mock(spec_set=["count", "offset", "limit", "all"])
        mock_query.count.side_effect = lambda: mock.sentinel.total
        mock_query.offset.side_effect = lambda n: mock_query
        mock_query.limit.side_effect = lambda n: mock_query
        mock_query.all.side_effect = lambda: mock.sentinel.all
        return mock_query

    @pytest.fixture
    def view_callable(self, query):
        """Return a mock view callable for paginate_query() to wrap."""
        view_callable = mock.Mock(return_value=query, spec_set=["__call__", "__name__"])
        view_callable.__name__ = "mock_view_callable"
        return view_callable

    @pytest.fixture
    def wrapped(self, view_callable):
        """Return a mock view callable wrapped in paginate_query()."""
        return paginate_query(view_callable, self.PAGE_SIZE)

from unittest import mock

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound
from webob.multidict import MultiDict

from h.activity.query import check_url, execute, extract, fetch_annotations


class TestExtract:
    def test_parses_param_value_with_parser(self, parse, pyramid_request):
        pyramid_request.GET["q"] = "giraffe"

        extract(pyramid_request, parse=parse)

        parse.assert_called_once_with("giraffe")

    def test_returns_empty_results_when_q_param_is_missing(
        self, parse, pyramid_request
    ):
        result = extract(pyramid_request, parse=parse)
        assert result == parse.return_value

    def test_returns_parse_results(self, parse, pyramid_request):
        parse.return_value = {"foo": "bar"}
        pyramid_request.GET["q"] = "giraffe"

        result = extract(pyramid_request, parse=parse)

        assert result == {"foo": "bar"}

    def test_overrides_group_term_for_group_search_requests(
        self, parse, pyramid_request
    ):
        # If the query sent to a group search page includes a group, we override
        # it, because otherwise we'll display the union of the results for those
        # two groups, which makes no sense.
        parse.return_value = MultiDict({"foo": "bar", "group": "whattheusersent"})
        pyramid_request.matched_route.name = "group_read"
        pyramid_request.matchdict["pubid"] = "abcd1234"
        pyramid_request.GET["q"] = "giraffe"

        result = extract(pyramid_request, parse=parse)

        assert result.dict_of_lists() == {"foo": ["bar"], "group": ["abcd1234"]}

    def test_overrides_user_term_for_user_search_requests(self, parse, pyramid_request):
        # If the query sent to a user search page includes a user, we override
        # it, because otherwise we'll display the union of the results for those
        # two users, which makes no sense.
        parse.return_value = MultiDict({"foo": "bar", "user": "whattheusersent"})
        pyramid_request.matched_route.name = "activity.user_search"
        pyramid_request.matchdict["username"] = "josiah"
        pyramid_request.GET["q"] = "giraffe"

        result = extract(pyramid_request, parse=parse)

        assert result.dict_of_lists() == {"foo": ["bar"], "user": ["josiah"]}

    @pytest.fixture
    def parse(self):
        return mock.Mock(spec_set=[], return_value=MultiDict({"foo": "bar"}))


@pytest.mark.usefixtures("routes", "user_service")
class TestCheckURL:
    def test_redirects_to_group_search_page_if_one_group_in_query(
        self, group, pyramid_request, unparse
    ):
        query = MultiDict({"group": group.pubid})

        with pytest.raises(HTTPFound) as e:
            check_url(pyramid_request, query, unparse=unparse)

        assert e.value.location == (
            f"/act/groups/{group.pubid}/{group.slug}?q=UNPARSED_QUERY"
        )

    def test_does_not_redirect_to_group_page_if_group_does_not_exist(
        self, pyramid_request, unparse
    ):
        query = MultiDict({"group": "does_not_exist"})

        assert check_url(pyramid_request, query, unparse=unparse) is None

    def test_does_not_remove_group_term_from_query_if_group_does_not_exist(
        self, pyramid_request, unparse
    ):
        query = MultiDict({"group": "does_not_exist"})

        check_url(pyramid_request, query, unparse=unparse)

        assert query.get("group") == "does_not_exist"
        assert not unparse.called

    def test_removes_group_term_from_query(self, group, pyramid_request, unparse):
        query = MultiDict({"group": group.pubid})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({})

    def test_preserves_other_query_terms_for_group_search(
        self, group, pyramid_request, unparse
    ):
        query = MultiDict({"group": group.pubid, "tag": "foo"})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({"tag": "foo"})

    def test_preserves_user_query_terms_for_group_search(
        self, group, pyramid_request, unparse
    ):
        query = MultiDict({"group": group.pubid, "user": "foo"})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({"user": "foo"})

    def test_redirects_to_user_search_page_if_one_user_in_query(
        self, pyramid_request, unparse
    ):
        query = MultiDict({"user": "jose"})

        with pytest.raises(HTTPFound) as e:
            check_url(pyramid_request, query, unparse=unparse)

        assert e.value.location == "/act/users/jose?q=UNPARSED_QUERY"

    def test_does_not_redirect_to_user_page_if_user_does_not_exist(
        self, pyramid_request, user_service
    ):
        query = MultiDict({"user": "jose"})
        user_service.fetch.return_value = None

        assert check_url(pyramid_request, query) is None

    def test_does_not_remove_user_term_from_query_if_user_does_not_exist(
        self, pyramid_request, unparse, user_service
    ):
        query = MultiDict({"user": "jose"})
        user_service.fetch.return_value = None

        check_url(pyramid_request, query, unparse=unparse)

        assert query.get("user") == "jose"
        assert not unparse.called

    def test_removes_user_term_from_query(self, pyramid_request, unparse):
        query = MultiDict({"user": "jose"})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({})

    def test_preserves_other_query_terms_for_user_search(
        self, pyramid_request, unparse
    ):
        query = MultiDict({"user": "jose", "tag": "foo"})

        with pytest.raises(HTTPFound):
            check_url(pyramid_request, query, unparse=unparse)

        unparse.assert_called_once_with({"tag": "foo"})

    def test_doesnt_raise_with_non_matching_queries(self, pyramid_request, unparse):
        query = MultiDict({"tag": "foo"})

        assert not check_url(pyramid_request, query, unparse=unparse)

    def test_doesnt_raise_if_not_on_search_page(self, pyramid_request, unparse):
        pyramid_request.matched_route.name = "group_read"
        query = MultiDict({"group": "abcd1234"})

        assert not check_url(pyramid_request, query, unparse=unparse)

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def unparse(self):
        return mock.Mock(spec_set=[], return_value="UNPARSED_QUERY")


@pytest.mark.usefixtures(
    "fetch_annotations",
    "_fetch_groups",
    "bucketing",
    "presenters",
    "AuthorityFilter",
    "Search",
    "TagsAggregation",
    "TopLevelAnnotationsFilter",
    "UsersAggregation",
    "links",
)
class TestExecute:

    PAGE_SIZE = 23

    def test_it_creates_a_search_query(self, pyramid_request, Search):
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        Search.assert_called_once_with(
            pyramid_request, separate_wildcard_uri_keys=False
        )

    def test_it_only_returns_top_level_annotations(
        self, pyramid_request, search, TopLevelAnnotationsFilter
    ):
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        TopLevelAnnotationsFilter.assert_called_once_with()
        search.append_modifier.assert_any_call(TopLevelAnnotationsFilter.return_value)

    def test_it_only_shows_annotations_from_default_authority(
        self, pyramid_request, search, AuthorityFilter
    ):
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        AuthorityFilter.assert_called_once_with(pyramid_request.default_authority)
        search.append_modifier.assert_any_call(AuthorityFilter.return_value)

    def test_it_adds_a_tags_aggregation_to_the_search_query(
        self, pyramid_request, search, TagsAggregation
    ):
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        TagsAggregation.assert_called_once_with(limit=50)
        search.append_aggregation.assert_called_with(TagsAggregation.return_value)

    def test_it_does_not_add_a_users_aggregation(
        self, pyramid_request, UsersAggregation
    ):
        """On non-group pages there's no users aggregations."""
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        assert not UsersAggregation.called

    def test_on_group_pages_it_adds_a_users_aggregation_to_the_search_query(
        self, pyramid_request, search, UsersAggregation
    ):
        """If there's a single group facet it adds a users aggregation."""
        query = MultiDict(group="foo")

        execute(pyramid_request, query, self.PAGE_SIZE)

        UsersAggregation.assert_called_once_with(limit=50)
        search.append_aggregation.assert_called_with(UsersAggregation.return_value)

    def test_it_limits_the_search_results_to_one_pages_worth(
        self, pyramid_request, search
    ):
        query = MultiDict()

        execute(pyramid_request, query, self.PAGE_SIZE)

        query = search.run.call_args[0][0]
        assert query["limit"] == self.PAGE_SIZE

    def test_it_gets_the_first_page_of_results_if_no_page_arg(
        self, pyramid_request, search
    ):
        query = MultiDict()
        assert "page" not in pyramid_request.params

        execute(pyramid_request, query, self.PAGE_SIZE)

        query = search.run.call_args[0][0]
        assert not query["offset"]

    def test_it_gets_the_first_page_of_results_if_page_arg_is_1(
        self, pyramid_request, search
    ):
        query = MultiDict()
        pyramid_request.params["page"] = "1"

        execute(pyramid_request, query, self.PAGE_SIZE)

        query = search.run.call_args[0][0]
        assert not query["offset"]

    @pytest.mark.parametrize(
        "page,offset",
        [
            ("2", 23),  # These expected offsets all assume a page size of 23.
            ("12", 253),
            ("1000", 22977),
        ],
    )
    def test_it_gets_the_nth_page_of_results_if_page_arg_is_n(
        self, pyramid_request, search, page, offset
    ):
        query = MultiDict()
        pyramid_request.params["page"] = page

        execute(pyramid_request, query, self.PAGE_SIZE)

        query = search.run.call_args[0][0]
        assert query["offset"] == offset

    @pytest.mark.parametrize("page", ("-1", "-3", "-2377"))
    def test_it_gets_the_first_page_of_results_if_page_arg_is_negative(
        self, pyramid_request, search, page
    ):
        query = MultiDict()
        pyramid_request.params["page"] = page

        execute(pyramid_request, query, self.PAGE_SIZE)

        query = search.run.call_args[0][0]
        assert not query["offset"]

    @pytest.mark.parametrize("page", ("-23.7", "foo"))
    def test_it_gets_the_first_page_of_results_if_page_arg_is_not_an_int(
        self, pyramid_request, search, page
    ):
        query = MultiDict()
        pyramid_request.params["page"] = page

        execute(pyramid_request, query, self.PAGE_SIZE)

        query = search.run.call_args[0][0]
        assert not query["offset"]

    def test_it_passes_the_given_query_params_to_the_search(
        self, pyramid_request, search
    ):
        query = MultiDict(foo="bar")

        execute(pyramid_request, query, self.PAGE_SIZE)

        assert search.run.call_args[0][0]["foo"] == "bar"

    def test_it_returns_the_search_result_if_there_are_no_matches(
        self, pyramid_request, search
    ):
        search.run.return_value.total = 0
        search.run.return_value.annotation_ids = []

        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        # This is what execute()'s result should look like if there are no
        # annotations that match the given search query.
        assert not result.total
        assert result.aggregations == mock.sentinel.aggregations
        assert result.timeframes == []

    def test_it_fetches_the_annotations_from_the_database(
        self, fetch_annotations, pyramid_request, search
    ):
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        fetch_annotations.assert_called_once_with(
            pyramid_request.db, search.run.return_value.annotation_ids
        )

    def test_it_buckets_the_annotations(
        self, fetch_annotations, bucketing, pyramid_request
    ):
        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        bucketing.bucket.assert_called_once_with(fetch_annotations.return_value)
        assert result.timeframes == bucketing.bucket.return_value

    def test_it_fetches_the_groups_from_the_database(
        self, _fetch_groups, group_pubids, pyramid_request
    ):
        execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        _fetch_groups.assert_called_once_with(
            pyramid_request.db, Any.iterable.containing(group_pubids).only()
        )

    def test_it_returns_each_annotation_presented(self, annotations, pyramid_request):
        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        presented_annotations = []
        for timeframe in result.timeframes:
            for bucket in timeframe.document_buckets.values():
                presented_annotations.extend(bucket.presented_annotations)

        for annotation in annotations:
            for presented_annotation in presented_annotations:
                if presented_annotation["annotation"].annotation == annotation:
                    break
            else:
                assert False

    def test_it_returns_each_annotations_group(self, _fetch_groups, pyramid_request):
        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        presented_annotations = []
        for timeframe in result.timeframes:
            for bucket in timeframe.document_buckets.values():
                presented_annotations.extend(bucket.presented_annotations)

        for group in _fetch_groups.return_value:
            for presented_annotation in presented_annotations:
                if presented_annotation["group"] == group:
                    break
            else:
                assert False

    def test_it_returns_each_annotations_incontext_link(self, links, pyramid_request):
        def incontext_link(request, annotation):
            assert (
                request == pyramid_request
            ), "It should always pass the request to incontext_link"
            # Return a predictable per-annotation value for the incontext link.
            return f"incontext_link_for_annotation_{annotation.id}"

        links.incontext_link.side_effect = incontext_link

        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        presented_annotations = []
        for timeframe in result.timeframes:
            for bucket in timeframe.document_buckets.values():
                presented_annotations.extend(bucket.presented_annotations)

        for presented_annotation in presented_annotations:
            assert presented_annotation["incontext_link"] == (
                f"incontext_link_for_annotation_{presented_annotation['annotation'].annotation.id}"
            )

    def test_it_returns_each_annotations_html_link(self, links, pyramid_request):
        def html_link(request, annotation):
            assert (
                request == pyramid_request
            ), "It should always pass the request to html_link"
            # Return a predictable per-annotation value for the html link.
            return f"html_link_for_annotation_{annotation.id}"

        links.html_link.side_effect = html_link

        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        presented_annotations = []
        for timeframe in result.timeframes:
            for bucket in timeframe.document_buckets.values():
                presented_annotations.extend(bucket.presented_annotations)

        for presented_annotation in presented_annotations:
            assert presented_annotation["html_link"] == (
                f"html_link_for_annotation_{presented_annotation['annotation'].annotation.id}"
            )

    def test_it_returns_the_total_number_of_matching_annotations(self, pyramid_request):
        assert execute(pyramid_request, MultiDict(), self.PAGE_SIZE).total == 20

    def test_it_returns_the_aggregations(self, pyramid_request):
        result = execute(pyramid_request, MultiDict(), self.PAGE_SIZE)

        assert result.aggregations == mock.sentinel.aggregations

    @pytest.fixture
    def fetch_annotations(self, patch):
        return patch("h.activity.query.fetch_annotations")

    @pytest.fixture
    def _fetch_groups(self, group_pubids, patch):
        _fetch_groups = patch("h.activity.query._fetch_groups")
        _fetch_groups.return_value = [mock.Mock(pubid=pubid) for pubid in group_pubids]
        return _fetch_groups

    @pytest.fixture
    def annotations(self, factories, group_pubids):
        """
        Return the 20 annotations that bucket() will return.

        Return a single flat list of all 20 annotations that will be
        distributed among the timeframes and document buckets that our mock
        bucketing.bucket() will return.

        """
        return [
            factories.Annotation.build(id="annotation_" + str(i), groupid=group_pubid)
            for i, group_pubid in enumerate(group_pubids)
        ]

    @pytest.fixture
    def bucketing(self, document_buckets, patch):
        bucketing = patch("h.activity.query.bucketing")

        def timeframe(document_buckets):
            """Return a mock timeframe like the ones that bucket() returns."""
            return mock.Mock(
                spec_set=["document_buckets"], document_buckets=document_buckets
            )

        timeframes = [
            timeframe(
                {
                    "Test Document 1": document_buckets[0],
                    "Test Document 2": document_buckets[1],
                    "Test Document 3": document_buckets[2],
                }
            ),
            timeframe({"Test Document 1": document_buckets[3]}),
            timeframe(
                {
                    "Test Document 4": document_buckets[4],
                    "Test Document 3": document_buckets[5],
                    "Test Document 5": document_buckets[6],
                }
            ),
        ]

        bucketing.bucket.return_value = timeframes

        return bucketing

    @pytest.fixture
    def document_buckets(self, annotations):
        """
        Return the 7 document buckets that bucket() will return.

        Return a single flat list of all 7 document buckets that will be
        distributed among the timeframes that our mock bucketing.bucket() will
        return.

        """

        def document_bucket(annotations):
            """Return a mock document bucket like the ones bucket() returns."""
            return mock.Mock(
                spec_set=["annotations", "presented_annotations"],
                annotations=annotations,
            )

        return [
            document_bucket(annotations[:3]),
            document_bucket(annotations[3:7]),
            document_bucket(annotations[7:12]),
            document_bucket(annotations[12:13]),
            document_bucket(annotations[13:15]),
            document_bucket(annotations[15:18]),
            document_bucket(annotations[18:]),
        ]

    @pytest.fixture
    def group_pubids(self):
        """
        Return a flat list of the pubids of all the annotations' groups.

        Return a single flat list of all 20 pubids of the groups of the
        annotations that our mock bucket() will return.

        """
        return ["group_" + str(i) for i in range(20)]

    @pytest.fixture
    def presenters(self, patch):
        presenters = patch("h.activity.query.presenters")
        presenters.AnnotationHTMLPresenter = mock.Mock(
            spec_set=["__call__"],
            side_effect=lambda annotation: mock.Mock(annotation=annotation),
        )
        return presenters

    @pytest.fixture
    def search(self, annotations):
        search = mock.Mock(spec_set=["append_modifier", "append_aggregation", "run"])
        search.run.return_value = mock.Mock(
            spec_set=["total", "aggregations", "annotation_ids"]
        )
        search.run.return_value.total = 20
        search.run.return_value.aggregations = mock.sentinel.aggregations
        search.run.return_value.annotation_ids = [
            annotation.id for annotation in annotations
        ]
        return search

    @pytest.fixture
    def Search(self, patch, search):
        return patch("h.activity.query.Search", return_value=search)

    @pytest.fixture
    def TagsAggregation(self, patch):
        return patch("h.activity.query.TagsAggregation")

    @pytest.fixture
    def AuthorityFilter(self, patch):
        return patch("h.activity.query.AuthorityFilter")

    @pytest.fixture
    def TopLevelAnnotationsFilter(self, patch):
        return patch("h.activity.query.TopLevelAnnotationsFilter")

    @pytest.fixture
    def UsersAggregation(self, patch):
        return patch("h.activity.query.UsersAggregation")

    @pytest.fixture
    def links(self, patch):
        return patch("h.activity.query.links")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        return pyramid_request


class TestFetchAnnotations:
    def test_it_returns_annotations_by_ids(self, db_session, factories):
        annotations = factories.Annotation.create_batch(3)
        ids = [a.id for a in annotations]

        result = fetch_annotations(db_session, ids)

        assert annotations == result


@pytest.fixture
def pyramid_request(pyramid_request):
    class DummyRoute:
        name = "activity.search"

    pyramid_request.matched_route = DummyRoute()
    return pyramid_request


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/act/groups/{pubid}/{slug}")
    pyramid_config.add_route("activity.user_search", "/act/users/{username}")

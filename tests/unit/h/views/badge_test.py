from datetime import datetime
from unittest import mock

import pytest
from pyramid import httpexceptions
from webob.multidict import MultiDict

from h.views.badge import Blocklist, badge


class TestBlocklist:
    @pytest.mark.parametrize("domain", Blocklist.BLOCKED_DOMAINS)
    @pytest.mark.parametrize("prefix", ("http://", "https://", "httpx://", "//"))
    @pytest.mark.parametrize("suffix", ("", "/", "/path?a=b"))
    def test_it_blocks_bad_domains(self, domain, prefix, suffix):
        assert Blocklist.is_blocked(f"{prefix}{domain}{suffix}")

    @pytest.mark.parametrize("scheme", Blocklist.BLOCKED_SCHEMES)
    @pytest.mark.parametrize("suffix", ("://about", "://newtab"))
    def test_it_blocks_bad_schema(self, scheme, suffix):
        assert Blocklist.is_blocked(f"{scheme}://{suffix}")

    @pytest.mark.parametrize(
        "acceptable_url",
        (
            "http://example.com/this/is/fine",
            "http://example.com//facebook.com",
            "http://facebook.com.om.nom",
            "file://c/my/magical_file.pdf",
            "chrome-extension://blah",
        ),
    )
    def test_it_allows_non_blocked_items(self, acceptable_url):
        assert not Blocklist.is_blocked(acceptable_url)

    def test_regex_golden_master(self):
        # This is a golden master test intended to facilitate refactoring
        # It just states that the regex is what it last was, this allows you
        # to change how it's generated and test if you have changed what is
        # generated
        assert Blocklist._PATTERN.pattern == (  # pylint:disable=protected-access
            r"^(?:(?:chrome)://)|(?:(?:http[sx]?:)?//"
            r"(?:(?:facebook\.com)|(?:www\.facebook\.com)|(?:mail\.google\.com))"
            r"(?:/|$))"
        )

    def test_its_fast(self):
        # Check any modifications haven't made this significantly slower
        reps = 10000

        start = datetime.utcnow()
        for _ in range(reps):
            Blocklist.is_blocked("http://example.com/this/is/fine")

        diff = datetime.utcnow() - start

        seconds = diff.seconds + diff.microseconds / 1000000
        calls_per_second = int(reps // seconds)

        # Handy to know while tinkering
        # print(
        #     f"Calls per second: {calls_per_second}, "
        #     f"{1000000 / calls_per_second:.03f} μs/call"
        # )

        # It should be above this number by quite a margin (20x), but we
        # don't want flaky tests
        assert calls_per_second > 50000


class TestBadge:
    def test_it_returns_0_if_blocked(self, badge_request, Blocklist, search_run):
        result = badge_request("http://example.com", annotated=True, blocked=True)

        Blocklist.is_blocked.assert_called_with("http://example.com")
        search_run.assert_not_called()
        assert result == {"total": 0}

    def test_it_sets_cache_headers_if_blocked(self, badge_request, pyramid_request):
        badge_request("http://example.com", annotated=True, blocked=True)

        cache_control = pyramid_request.response.cache_control

        assert cache_control.prevent_auto
        assert cache_control.public
        assert cache_control.max_age > 0

    def test_it_returns_0_if_uri_never_annotated(self, badge_request, search_run):
        result = badge_request("http://example.com", annotated=False, blocked=False)

        search_run.assert_not_called()
        assert result == {"total": 0}

    def test_it_returns_number_from_search(self, badge_request, search_run):
        result = badge_request("http://example.com", annotated=True, blocked=False)

        search_run.assert_called_once_with(
            MultiDict({"uri": "http://example.com", "limit": 0})
        )
        assert result == {"total": search_run.return_value.total}

    def test_it_raises_if_no_uri(self):
        with pytest.raises(httpexceptions.HTTPBadRequest):
            badge(mock.Mock(params={}))

    @pytest.fixture
    def badge_request(self, pyramid_request, factories, Blocklist):
        def caller(uri, annotated=True, blocked=False):
            if annotated:
                factories.DocumentURI(uri=uri)
                pyramid_request.db.flush()

            Blocklist.is_blocked.return_value = blocked

            pyramid_request.params["uri"] = uri
            return badge(pyramid_request)

        return caller

    @pytest.fixture(autouse=True)
    def Blocklist(self, patch):
        return patch("h.views.badge.Blocklist")

    @pytest.fixture(autouse=True)
    def search_run(self, patch):
        search_lib = patch("h.views.badge.search")

        search_run = search_lib.Search.return_value.run
        search_run.return_value = mock.Mock(total=29)
        return search_run

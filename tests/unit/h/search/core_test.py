"""
Tests for basic functionality of the `Search` class.

Tests for filtering/matching/aggregating on specific annotation fields are in
`query_test.py`.
"""

import datetime

import pytest
from h_matchers import Any
from webob.multidict import MultiDict

from h import search

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


@pytest.mark.usefixtures("group_service", "nipsa_service")
class TestSearch:
    """Unit tests for search.Search when no separate_replies argument is given."""

    def test_it_defaults_separate_wildcard_uri_keys_to_true(
        self, pyramid_request, UriCombinedWildcardFilter
    ):
        separate_keys = True

        search.Search(pyramid_request)

        UriCombinedWildcardFilter.assert_called_once_with(
            pyramid_request, separate_keys
        )

    def test_it_passes_separate_wildcard_uri_keys_to_filter(
        self, pyramid_request, UriCombinedWildcardFilter
    ):
        separate_keys = False

        search.Search(pyramid_request, separate_wildcard_uri_keys=separate_keys)

        UriCombinedWildcardFilter.assert_called_once_with(
            pyramid_request, separate_keys
        )

    def test_it_returns_replies_in_annotations_ids(self, pyramid_request, Annotation):
        """
        Without separate_replies it returns replies in annotation_ids.

        Test that if no separate_replies argument is given then it returns the
        ids of replies mixed in with the top-level annotations in
        annotation_ids.
        """
        annotation = Annotation(shared=True)
        reply_1 = Annotation(shared=True, references=[annotation.id])
        reply_2 = Annotation(shared=True, references=[annotation.id])

        result = search.Search(pyramid_request).run(MultiDict({}))

        assert (
            result.annotation_ids
            == Any.list.containing([annotation.id, reply_1.id, reply_2.id]).only()
        )

    def test_replies_that_dont_match_the_search_arent_included(
        self, factories, pyramid_request, Annotation
    ):
        """
        Replies that don't match the search query aren't included.

        Not even if the top-level annotations that they're replies to _are_
        included.
        """
        user = factories.User()
        reply_user = factories.User()
        annotation = Annotation(userid=user.userid, shared=True)
        reply = Annotation(
            userid=reply_user.userid, references=[annotation.id], shared=True
        )

        result = search.Search(pyramid_request).run(
            # Search for annotations from ``user``, so that ``reply_user``'s
            # reply doesn't match.
            params=MultiDict({"user": user.userid})
        )

        assert reply.id not in result.annotation_ids

    def test_replies_from_different_pages_arent_included(
        self, pyramid_request, Annotation
    ):
        """Replies may not be on the same page of results as their annotations."""
        # First create an annotation and a reply.
        annotation = Annotation(shared=True)
        reply = Annotation(references=[annotation.id], shared=True)

        # Now create 19 more annotations so that the original annotation is
        # pushed onto the second page of the search results, but the reply is
        # still on the first page.
        for _ in range(19):
            Annotation(shared=True)

        # The reply is on the first page of search results, but the original annotation isn't.
        result = search.Search(pyramid_request).run(
            params=MultiDict({"offset": 0, "limit": 20})
        )
        assert reply.id in result.annotation_ids
        assert annotation.id not in result.annotation_ids

        # The original annotation is on the second page of search results, but the reply isn't.
        result = search.Search(pyramid_request).run(params=MultiDict({"offset": 20}))
        assert reply.id not in result.annotation_ids
        assert annotation.id in result.annotation_ids

    def test_replies_can_come_before_annotations(self, pyramid_request, Annotation):
        """
        A reply may appear before its annotation in the search results.

        Things are returned in updated order so normally a reply would appear
        before the annotation that it is a reply to in the search results.
        """
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        annotation = Annotation(updated=now, shared=True)
        reply = Annotation(
            updated=now + five_mins, references=[annotation.id], shared=True
        )

        result = search.Search(pyramid_request).run(MultiDict({}))

        # The reply appears _before_ the annotation in the search results.
        assert result.annotation_ids == [reply.id, annotation.id]

    def test_replies_can_come_after_annotations(self, pyramid_request, Annotation):
        """
        A reply may appear after its annotation in the search results.

        Things are returned in updated order so if the original author has
        updated the top-level annotation since the reply was created, then the
        annotation would come before the reply in the search results.
        """
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        annotation = Annotation(updated=now + five_mins, shared=True)
        reply = Annotation(updated=now, references=[annotation.id], shared=True)

        result = search.Search(pyramid_request).run(MultiDict({}))

        # The reply appears _after_ the annotation in the search results.
        assert result.annotation_ids == [annotation.id, reply.id]

    def test_it_returns_an_empty_replies_list(self, pyramid_request, Annotation):
        """
        Test that without separate_replies it returns an empty reply_ids.

        If no separate_replies argument is given then it still returns a
        reply_ids list but the list is always empty.
        """
        annotation = Annotation(shared=True)
        Annotation(references=[annotation.id], shared=True)
        Annotation(references=[annotation.id], shared=True)

        result = search.Search(pyramid_request).run(MultiDict({}))

        assert result.reply_ids == []

    @pytest.fixture
    def UriCombinedWildcardFilter(self, patch):
        return patch("h.search.core.query.UriCombinedWildcardFilter")


@pytest.mark.usefixtures("group_service", "nipsa_service")
class TestSearchWithSeparateReplies:
    """Unit tests for search.Search when separate_replies=True is given."""

    def test_it_returns_replies_separately_from_annotations(
        self, pyramid_request, Annotation
    ):
        """If separate_replies=True replies and annotations are returned separately."""
        annotation = Annotation(shared=True)
        reply_1 = Annotation(references=[annotation.id], shared=True)
        reply_2 = Annotation(references=[annotation.id], shared=True)

        result = search.Search(pyramid_request, separate_replies=True).run(
            MultiDict({})
        )

        assert result.annotation_ids == [annotation.id]
        assert result.reply_ids == Any.list.containing([reply_1.id, reply_2.id]).only()

    def test_replies_are_ordered_most_recently_updated_first(
        self, Annotation, pyramid_request
    ):
        annotation = Annotation(shared=True)
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        reply_1 = Annotation(
            updated=now + (five_mins * 2), references=[annotation.id], shared=True
        )
        reply_2 = Annotation(updated=now, references=[annotation.id], shared=True)
        reply_3 = Annotation(
            updated=now + five_mins, references=[annotation.id], shared=True
        )

        result = search.Search(pyramid_request, separate_replies=True).run(
            MultiDict({})
        )

        assert result.reply_ids == [reply_1.id, reply_3.id, reply_2.id]

    def test_replies_ignore_the_sort_param(self, Annotation, pyramid_request):
        annotation = Annotation(shared=True)
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        reply_1 = Annotation(
            id="3", updated=now, references=[annotation.id], shared=True
        )
        reply_2 = Annotation(
            id="1", updated=now + five_mins, references=[annotation.id], shared=True
        )
        reply_3 = Annotation(
            id="2",
            updated=now + (five_mins * 2),
            references=[annotation.id],
            shared=True,
        )

        result = search.Search(pyramid_request, separate_replies=True).run(
            MultiDict({"sort": "id", "order": "asc"})
        )

        assert result.reply_ids == [reply_3.id, reply_2.id, reply_1.id]

    def test_separate_replies_that_dont_match_the_search_are_still_included(
        self, factories, pyramid_request, Annotation
    ):
        """
        All replies to the matching annotations are included.

        Even if the replies don't match the search query. As long as the
        top-level annotation matches the search query, its replies will be
        included in reply_ids.
        """
        user = factories.User()
        reply_user = factories.User()
        annotation = Annotation(userid=user.userid, shared=True)
        reply = Annotation(
            userid=reply_user.userid, references=[annotation.id], shared=True
        )

        result = search.Search(pyramid_request, separate_replies=True).run(
            # The reply would not match this search query because it's from
            # ``reply_user`` not ``user``.
            params=MultiDict({"user": user.userid})
        )

        assert result.reply_ids == [reply.id]

    def test_replies_from_different_pages_are_included(
        self, pyramid_request, Annotation
    ):
        """Replies that would not be on the same page are included."""
        # First create an annotation and a reply.
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        annotation = Annotation(updated=now + five_mins, shared=True)
        reply = Annotation(updated=now, references=[annotation.id], shared=True)

        # Now create 19 more annotations. Without separate_replies the
        # annotation would be the 20th item in the search results (last item on
        # the first page) and the reply would be pushed onto the second page.
        for _ in range(19):
            Annotation(shared=True)

        result = search.Search(pyramid_request, separate_replies=True).run(
            params=MultiDict({"limit": 20})
        )

        # Even though the reply would have been on the second page of the
        # search results, it is still included in reply_ids if
        # separate_replies=True.
        assert result.reply_ids == [reply.id]

    def test_only_200_replies_are_included(self, pyramid_request, Annotation):
        """
        No more than 200 replies can be included in reply_ids.

        200 is the total maximum number of replies (to all annotations in
        annotation_ids) that can be included in reply_ids.
        """
        annotation = Annotation(shared=True)
        oldest_reply = Annotation(references=[annotation.id], shared=True)

        # Create three more replies so that the oldest reply will be pushed out
        # of reply_ids. (We only need 3, not 200, because we're going to use
        # the _replies_limit test seam to limit it to 3 replies instead of 200.
        # This is just to make the test faster.)
        for _ in range(3):
            Annotation(references=[annotation.id], shared=True)

        result = search.Search(
            pyramid_request, separate_replies=True, _replies_limit=3
        ).run(MultiDict({}))

        assert len(result.reply_ids) == 3
        assert oldest_reply.id not in result.reply_ids

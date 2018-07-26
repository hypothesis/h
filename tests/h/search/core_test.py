# -*- coding: utf-8 -*-

"""
Tests for basic functionality of the `Search` class.

Tests for filtering/matching/aggregating on specific annotation fields are in
`query_test.py`.
"""

from __future__ import unicode_literals

import datetime
import pytest

from h import search


class TestSearch(object):
    """Unit tests for search.Search when no separate_replies argument is given."""

    def test_it_returns_replies_in_annotations_ids(self, matchers, pyramid_request, Annotation):
        """Without separate_replies it returns replies in annotation_ids.

        Test that if no separate_replies argument is given then it returns the
        ids of replies mixed in with the top-level annotations in
        annotation_ids.
        """
        annotation = Annotation(shared=True)
        reply_1 = Annotation(shared=True, references=[annotation.id])
        reply_2 = Annotation(shared=True, references=[annotation.id])

        result = search.Search(pyramid_request).run({})

        assert result.annotation_ids == matchers.UnorderedList([annotation.id, reply_1.id,
                                                                reply_2.id])

    def test_replies_that_dont_match_the_search_arent_included(self, factories, pyramid_request,
                                                               Annotation):
        """Replies that don't match the search query aren't included.

        Not even if the top-level annotations that they're replies to _are_
        included.
        """
        user = factories.User()
        reply_user = factories.User()
        annotation = Annotation(userid=user.userid, shared=True)
        reply = Annotation(userid=reply_user.userid, references=[annotation.id], shared=True)

        result = search.Search(pyramid_request).run(
            # Search for annotations from ``user``, so that ``reply_user``'s
            # reply doesn't match.
            params={"user": user.userid},
        )

        assert reply.id not in result.annotation_ids

    def test_replies_from_different_pages_arent_included(self, pyramid_request, Annotation):
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
        result = search.Search(pyramid_request).run(params={"offset": 0, "limit": 20})
        assert reply.id in result.annotation_ids
        assert annotation.id not in result.annotation_ids

        # The original annotation is on the second page of search results, but the reply isn't.
        result = search.Search(pyramid_request).run(params={"offset": 20})
        assert reply.id not in result.annotation_ids
        assert annotation.id in result.annotation_ids

    def test_replies_can_come_before_annotations(self, pyramid_request, Annotation):
        """A reply may appear before its annotation in the search results.

        Things are returned in updated order so normally a reply would appear
        before the annotation that it is a reply to in the search results.
        """
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        annotation = Annotation(updated=now, shared=True)
        reply = Annotation(updated=now + five_mins, references=[annotation.id], shared=True)

        result = search.Search(pyramid_request).run({})

        # The reply appears _before_ the annotation in the search results.
        assert result.annotation_ids == [reply.id, annotation.id]

    def test_replies_can_come_after_annotations(self, pyramid_request, Annotation):
        """A reply may appear after its annotation in the search results.

        Things are returned in updated order so if the original author has
        updated the top-level annotation since the reply was created, then the
        annotation would come before the reply in the search results.
        """
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        annotation = Annotation(updated=now + five_mins, shared=True)
        reply = Annotation(updated=now, references=[annotation.id], shared=True)

        result = search.Search(pyramid_request).run({})

        # The reply appears _after_ the annotation in the search results.
        assert result.annotation_ids == [annotation.id, reply.id]

    def test_it_returns_an_empty_replies_list(self, pyramid_request, Annotation):
        """Test that without separate_replies it returns an empty reply_ids.

        If no separate_replies argument is given then it still returns a
        reply_ids list but the list is always empty.
        """
        annotation = Annotation(shared=True)
        Annotation(references=[annotation.id], shared=True)
        Annotation(references=[annotation.id], shared=True)

        result = search.Search(pyramid_request).run({})

        assert result.reply_ids == []

    def test_it_passes_es_version_to_builder(self, pyramid_request, Builder):
        client = pyramid_request.es
        if pyramid_request.feature('search_es6'):
            client = pyramid_request.es6

        search.Search(pyramid_request)

        assert Builder.call_count == 2
        Builder.assert_any_call(es_version=client.version)

    @pytest.fixture
    def Builder(self, patch):
        return patch('h.search.core.query.Builder', autospec=True)


class TestSearchWithSeparateReplies(object):
    """Unit tests for search.Search when separate_replies=True is given."""

    def test_it_returns_replies_separately_from_annotations(self, matchers, pyramid_request,
                                                            Annotation):
        """If separate_replies=True replies and annotations are returned separately."""
        annotation = Annotation(shared=True)
        reply_1 = Annotation(references=[annotation.id], shared=True)
        reply_2 = Annotation(references=[annotation.id], shared=True)

        result = search.Search(pyramid_request, separate_replies=True).run({})

        assert result.annotation_ids == [annotation.id]
        assert result.reply_ids == matchers.UnorderedList([reply_1.id, reply_2.id])

    def test_replies_are_ordered_most_recently_updated_first(self, Annotation, pyramid_request):
        annotation = Annotation(shared=True)
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        reply_1 = Annotation(updated=now + (five_mins * 2), references=[annotation.id], shared=True)
        reply_2 = Annotation(updated=now, references=[annotation.id], shared=True)
        reply_3 = Annotation(updated=now + five_mins, references=[annotation.id], shared=True)

        result = search.Search(pyramid_request, separate_replies=True).run({})

        assert result.reply_ids == [reply_1.id, reply_3.id, reply_2.id]

    def test_replies_ignore_the_sort_param(self, Annotation, pyramid_request):
        annotation = Annotation(shared=True)
        now = datetime.datetime.now()
        five_mins = datetime.timedelta(minutes=5)
        reply_1 = Annotation(id="3", updated=now, references=[annotation.id], shared=True)
        reply_2 = Annotation(id="1", updated=now + five_mins, references=[annotation.id],
                             shared=True)
        reply_3 = Annotation(id="2", updated=now + (five_mins * 2), references=[annotation.id],
                             shared=True)

        result = search.Search(pyramid_request, separate_replies=True).run({
            "sort": "id", "order": "asc",
        })

        assert result.reply_ids == [reply_3.id, reply_2.id, reply_1.id]

    def test_separate_replies_that_dont_match_the_search_are_still_included(self, factories,
                                                                            pyramid_request,
                                                                            Annotation):
        """All replies to the matching annotations are included.

        Even if the replies don't match the search query. As long as the
        top-level annotation matches the search query, its replies will be
        included in reply_ids.
        """
        user = factories.User()
        reply_user = factories.User()
        annotation = Annotation(userid=user.userid, shared=True)
        reply = Annotation(userid=reply_user.userid, references=[annotation.id], shared=True)

        result = search.Search(pyramid_request, separate_replies=True).run(
            # The reply would not match this search query because it's from
            # ``reply_user`` not ``user``.
            params={"user": user.userid},
        )

        assert result.reply_ids == [reply.id]

    def test_replies_from_different_pages_are_included(self, pyramid_request, Annotation):
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

        result = search.Search(pyramid_request, separate_replies=True).run(params={"limit": 20})

        # Even though the reply would have been on the second page of the
        # search results, it is still included in reply_ids if
        # separate_replies=True.
        assert result.reply_ids == [reply.id]

    def test_only_200_replies_are_included(self, pyramid_request, Annotation):
        """No more than 200 replies can be included in reply_ids.

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

        result = search.Search(pyramid_request, separate_replies=True, _replies_limit=3).run({})

        assert len(result.reply_ids) == 3
        assert oldest_reply.id not in result.reply_ids


@pytest.fixture(params=['es1', 'es6'])
def pyramid_request(request, pyramid_request, es_client, es6_client):
    pyramid_request.es = es_client
    pyramid_request.es6 = es6_client
    pyramid_request.feature.flags["search_es6"] = request.param == 'es6'
    return pyramid_request

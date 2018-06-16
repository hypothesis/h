# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import webob

from h import search


class TestTopLevelAnnotationsFilter(object):

    def test_it_filters_out_replies_but_leaves_annotations_in(self, Annotation, search):
        annotation = Annotation(shared=True)
        reply = Annotation(references=[annotation.id], shared=True)

        result = search.run({})

        assert annotation.id in result.annotation_ids
        assert reply.id not in result.annotation_ids

    @pytest.fixture
    def search(self, pyramid_request):
        search_ = search.Search(pyramid_request)
        search_.append_filter(search.TopLevelAnnotationsFilter())
        return search_


class TestAuthorityFilter(object):
    def test_it_filters_out_non_matching_authorities(self, Annotation, search):
        annotations_auth1 = [Annotation(userid="acct:foo@auth1", shared=True).id,
                             Annotation(userid="acct:bar@auth1", shared=True).id]
        # Make some other annotations that are of different authority.
        Annotation(userid="acct:bat@auth2", shared=True)
        Annotation(userid="acct:bar@auth3", shared=True)

        result = search.run({})

        assert set(result.annotation_ids) == set(annotations_auth1)

    @pytest.fixture
    def search(self, pyramid_request):
        search_ = search.Search(pyramid_request)
        search_.append_filter(search.AuthorityFilter("auth1"))
        return search_


class TestAuthFilter(object):
    def test_logged_out_user_can_not_see_private_annotations(self, search, Annotation):
        Annotation()
        Annotation()

        result = search.run({})

        assert not result.annotation_ids

    def test_logged_out_user_can_see_shared_annotations(self, search, Annotation):
        shared_ids = [Annotation(shared=True).id,
                      Annotation(shared=True).id]

        result = search.run({})

        assert set(result.annotation_ids) == set(shared_ids)

    def test_logged_in_user_can_only_see_their_private_annotations(self, search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        # Make a private annotation from a different user.
        Annotation(userid="acct:foo@auth2").id
        users_private_ids = [Annotation(userid=userid).id,
                             Annotation(userid=userid).id]

        result = search.run({})

        assert set(result.annotation_ids) == set(users_private_ids)

    def test_logged_in_user_can_see_shared_annotations(self, search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        shared_ids = [Annotation(userid="acct:foo@auth2", shared=True).id,
                      Annotation(userid=userid, shared=True).id]

        result = search.run({})

        assert set(result.annotation_ids) == set(shared_ids)

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append AuthFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestGroupFilter(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append GroupFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestGroupAuthFilter(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append GroupAuthFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestUserFilter(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append UserFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestUriFilter(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append UriFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestDeletedFilter(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append DeletedFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestNipsaFilter(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append NipsaFilter to Search because it's one of the filters that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestAnyMatcher(object):

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append AnyMatcher to Search because it's one of the matchers that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestTagsMatcher(object):
    def test_matches_tag_key(self, search, Annotation):
        Annotation(shared=True)
        Annotation(shared=True, tags=["bar"])
        matched_ids = [Annotation(shared=True, tags=["foo"]).id,
                       Annotation(shared=True, tags=["foo", "bar"]).id]

        result = search.run({"tag": "foo"})

        assert set(result.annotation_ids) == set(matched_ids)

    def test_matches_tags_key(self, search, Annotation):
        Annotation(shared=True)
        Annotation(shared=True, tags=["bar"])
        matched_ids = [Annotation(shared=True, tags=["foo"]).id,
                       Annotation(shared=True, tags=["foo", "bar"]).id]

        result = search.run({"tags": "foo"})

        assert set(result.annotation_ids) == set(matched_ids)

    def test_ands_multiple_tag_keys(self, search, Annotation):
        Annotation(shared=True)
        Annotation(shared=True, tags=["bar"])
        Annotation(shared=True, tags=["baz"])
        Annotation(shared=True, tags=["boo"])
        matched_ids = [Annotation(shared=True, tags=["foo", "baz", "fie", "boo"]).id,
                       Annotation(shared=True, tags=["foo", "baz", "fie", "boo", "bar"]).id]

        params = webob.multidict.MultiDict()
        params.add("tags", "foo")
        params.add("tags", "boo")
        params.add("tag", "fie")
        params.add("tag", "baz")
        result = search.run(params)

        assert set(result.annotation_ids) == set(matched_ids)

    @pytest.fixture
    def search(self, pyramid_request):
        # We don't need to append TagsMatcher to Search because it's one of the matchers that
        # Search appends by default.
        return search.Search(pyramid_request)


class TestRepliesMatcher(object):

    # Note: tests will have to append a RepliesMatcher object to the search
    # (search.append_matcher(RepliesMatcher(annotation_ids))) passing to RepliesMatcher the
    # annotation_ids of the annotations that the test wants to search for replies to.

    @pytest.fixture
    def search(self, pyramid_request):
        return search.Search(pyramid_request)


class TestTagsAggregation(object):

    @pytest.fixture
    def search(self, pyramid_request):
        search_ = search.Search(pyramid_request)
        search_.append_aggregation(search.TagsAggregation())
        return search_


class TestUsersAggregation(object):

    @pytest.fixture
    def search(self, pyramid_request):
        search_ = search.Search(pyramid_request)
        search_.append_aggregation(search.UsersAggregation())
        return search_

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import webob

from h.search import Search, query


class TestTopLevelAnnotationsFilter(object):

    def test_it_filters_out_replies_but_leaves_annotations_in(self, Annotation, search):
        annotation = Annotation()
        reply = Annotation(references=[annotation.id])

        result = search.run({})

        assert annotation.id in result.annotation_ids
        assert reply.id not in result.annotation_ids

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.TopLevelAnnotationsFilter())
        return search


class TestAuthorityFilter(object):
    def test_it_filters_out_non_matching_authorities(self, Annotation, search):
        annotations_auth1 = [Annotation(userid="acct:foo@auth1").id,
                             Annotation(userid="acct:bar@auth1").id]
        # Make some other annotations that are of different authority.
        Annotation(userid="acct:bat@auth2")
        Annotation(userid="acct:bar@auth3")

        result = search.run({})

        assert set(result.annotation_ids) == set(annotations_auth1)

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.AuthorityFilter("auth1"))
        return search


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

    def test_logged_in_user_can_only_see_their_private_annotations(self,
            search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        # Make a private annotation from a different user.
        Annotation(userid="acct:foo@auth2").id
        users_private_ids = [Annotation(userid=userid).id,
                             Annotation(userid=userid).id]

        result = search.run({})

        assert set(result.annotation_ids) == set(users_private_ids)

    def test_logged_in_user_can_see_shared_annotations(self,
            search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        shared_ids = [Annotation(userid="acct:foo@auth2", shared=True).id,
                      Annotation(userid=userid, shared=True).id]

        result = search.run({})

        assert set(result.annotation_ids) == set(shared_ids)

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.AuthFilter(pyramid_request))
        return search


class TestGroupFilter(object):

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.GroupFilter())
        return search


class TestGroupAuthFilter(object):

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.GroupAuthFilter(pyramid_request))
        return search


class TestUserFilter(object):
    def test_filters_annotations_by_user(self, search, Annotation):
        Annotation(userid="acct:foo@auth2", shared=True)
        expected_ids = [Annotation(userid="acct:bar@auth2", shared=True).id]

        result = search.run({'user': "bar"})

        assert set(result.annotation_ids) == set(expected_ids)

    def test_filters_annotations_by_multiple_users(self, search, Annotation):
        Annotation(userid="acct:foo@auth2", shared=True)
        expected_ids = [Annotation(userid="acct:bar@auth2", shared=True).id,
                        Annotation(userid="acct:baz@auth2", shared=True).id]

        params = webob.multidict.MultiDict()
        params.add("user", "bar")
        params.add("user", "baz")
        result = search.run(params)

        assert set(result.annotation_ids) == set(expected_ids)

    def test_filters_annotations_by_user_and_authority(self, search, Annotation):
        Annotation(userid="acct:foo@auth2", shared=True)
        expected_ids = [Annotation(userid="acct:foo@auth3", shared=True).id]

        result = search.run({"user": "foo@auth3"})

        assert set(result.annotation_ids) == set(expected_ids)

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.UserFilter())
        return search


class TestUriFilter(object):
    def test_filters_by_uri(self, search, Annotation):
        Annotation(target_uri="http://bar.com")
        Annotation(target_uri="https://bar.com")
        Annotation(target_uri="https://foo/bar.com")
        expected_ids = [Annotation(target_uri="bar.com").id]

        result = search.run({"uri": "bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_by_url(self, search, Annotation):
        Annotation(target_uri="http://bar.com")
        Annotation(target_uri="https://bar.com")
        Annotation(target_uri="https://foo/bar.com")
        expected_ids = [Annotation(target_uri="bar.com").id]

        result = search.run({"url": "bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_on_whole_url(self, search, Annotation):
        Annotation(target_uri="http://bar.com")
        Annotation(target_uri="foo/bar.com")
        Annotation(target_uri="http://foo.com")
        expected_ids = [Annotation(target_uri="http://foo/bar.com").id]

        result = search.run({"url": "http://foo/bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_aliases_http_and_https(self, search, Annotation):
        Annotation(target_uri="bar.com")
        Annotation(target_uri="www.bar.com")
        expected_ids = [Annotation(target_uri="http://bar.com").id,
                        Annotation(target_uri="https://bar.com").id]

        result = search.run({"url": "http://bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filter_distinguishes_net_com_url(self, search, Annotation):
        Annotation(target_uri="example.com")
        Annotation(target_uri="https://example.net")
        expected_ids = [Annotation(target_uri="http://example.com").id]

        params = webob.multidict.MultiDict()
        params.add("url", "http://example.com")
        result = search.run(params)

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_ors_multiple_url_uris(self, search, Annotation):
        Annotation(target_uri="baz.com")
        Annotation(target_uri="www.foo.com")
        expected_ids = [Annotation(target_uri="bar.com").id,
                        Annotation(target_uri="bat.com").id,
                        Annotation(target_uri="https://foo.com").id,
                        Annotation(target_uri="http://foo.com").id,
                        Annotation(target_uri="http://foo/bar.com").id]

        params = webob.multidict.MultiDict()
        params.add("uri", "bat.com")
        params.add("uri", "bar.com")
        params.add("url", "http://foo.com")
        params.add("url", "https://foo/bar.com")
        result = search.run(params)

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.UriFilter(pyramid_request))
        return search


class TestDeletedFilter(object):

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.DeletedFilter())
        return search


class TestNipsaFilter(object):

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.NipsaFilter(pyramid_request))
        return search


class TestAnyMatcher(object):

    @pytest.fixture
    def search(self, search):
        search.append_matcher(query.AnyMatcher())
        return search


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
    def search(self, search):
        search.append_matcher(query.TagsMatcher())
        return search


class TestRepliesMatcher(object):

    # Note: tests will have to append a RepliesMatcher object to the search
    # (search.append_matcher(RepliesMatcher(annotation_ids))) passing to RepliesMatcher the
    # annotation_ids of the annotations that the test wants to search for replies to.
    pass


class TestTagsAggregation(object):

    @pytest.fixture
    def search(self, search):
        search.append_aggregation(query.TagsAggregation())
        return search


class TestUsersAggregation(object):

    @pytest.fixture
    def search(self, search):
        search.append_aggregation(query.UsersAggregation())
        return search


@pytest.fixture
def search(pyramid_request):
    search = Search(pyramid_request)
    # Remove all default filters, aggregators, and matchers.
    search.clear()
    return search

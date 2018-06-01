# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.search import Search, query


class TestTopLevelAnnotationsFilter(object):

    def test_it_filters_out_replies_but_leaves_annotations_in(self, Annotation, filtered_search):
        annotation = Annotation(shared=True)
        reply = Annotation(references=[annotation.id], shared=True)

        result = filtered_search.run({})

        assert annotation.id in result.annotation_ids
        assert reply.id not in result.annotation_ids

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.TopLevelAnnotationsFilter())
        return search


class TestAuthorityFilter(object):
    def test_it_filters_out_non_matching_authorities(self, Annotation, filtered_search):
        annotations_auth1 = [Annotation(userid="acct:foo@auth1", shared=True).id,
                             Annotation(userid="acct:bar@auth1", shared=True).id]
        # Make some other annotations that are of different authority.
        Annotation(userid="acct:bat@auth2", shared=True)
        Annotation(userid="acct:bar@auth3", shared=True)

        result = filtered_search.run({})

        assert set(result.annotation_ids) == set(annotations_auth1)

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.AuthorityFilter("auth1"))
        return search


class TestAuthFilter(object):
    def test_logged_out_user_can_not_see_private_annotations(self, filtered_search, Annotation):
        Annotation()
        Annotation()

        result = filtered_search.run({})

        assert not result.annotation_ids

    def test_logged_out_user_can_see_shared_annotations(self, filtered_search, Annotation):
        shared_ids = [Annotation(shared=True).id,
                      Annotation(shared=True).id]

        result = filtered_search.run({})

        assert set(result.annotation_ids) == set(shared_ids)

    def test_logged_in_user_can_only_see_their_private_annotations(self,
            filtered_search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        # Make a private annotation from a different user.
        Annotation(userid="acct:foo@auth2").id
        users_private_ids = [Annotation(userid=userid).id,
                             Annotation(userid=userid).id]

        result = filtered_search.run({})

        assert set(result.annotation_ids) == set(users_private_ids)

    def test_logged_in_user_can_see_shared_annotations(self,
            filtered_search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        shared_ids = [Annotation(userid="acct:foo@auth2", shared=True).id,
                      Annotation(userid=userid, shared=True).id]

        result = filtered_search.run({})

        assert set(result.annotation_ids) == set(shared_ids)

    @pytest.fixture
    def filtered_search(self, search, pyramid_request):
        search.append_filter(query.AuthFilter(pyramid_request))
        return search


class TestGroupFilter(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.GroupFilter())
        return search


class TestGroupAuthFilter(object):

    @pytest.fixture
    def filtered_search(self, search, pyramid_request):
        search.append_filter(query.GroupAuthFilter(pyramid_request))
        return search


class TestUserFilter(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.UserFilter())
        return search


class TestUriFilter(object):

    @pytest.fixture
    def filtered_search(self, search, pyramid_request):
        search.append_filter(query.UriFilter(pyramid_request))
        return search


class TestDeletedFilter(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.DeletedFilter())
        return search


class TestNipsaFilter(object):

    @pytest.fixture
    def filtered_search(self, search, pyramid_request):
        search.append_filter(query.NipsaFilter(pyramid_request))
        return search


class TestAnyMatcher(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.AnyMatcher())
        return search


class TestTagsMatcher(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_filter(query.TagsMatcher())
        return search


class TestRepliesMatcher(object):

    # Note: tests will have to append a RepliesMatcher object to the search
    # (search.append_matcher(RepliesMatcher(annotation_ids))) passing to RepliesMatcher the
    # annotation_ids of the annotations that the test wants to search for replies to.
    pass


class TestTagsAggregation(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_aggregation(query.TagsAggregation())
        return search


class TestUsersAggregation(object):

    @pytest.fixture
    def filtered_search(self, search):
        search.append_aggregation(query.UsersAggregation())
        return search


@pytest.fixture
def search(pyramid_request):
    search = Search(pyramid_request)
    # Remove all default filters, aggregators, and matchers.
    search.clear()
    return search

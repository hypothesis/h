# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import webob

from h.search import Search, index, query


class TestTopLevelAnnotationsFilter(object):

    def test_it_filters_out_replies_but_leaves_annotations_in(self, Annotation, search):
        annotation = Annotation()
        Annotation(references=[annotation.id])

        result = search.run({})

        assert [annotation.id] == result.annotation_ids

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

        assert sorted(result.annotation_ids) == sorted(annotations_auth1)

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

        assert sorted(result.annotation_ids) == sorted(shared_ids)

    def test_logged_in_user_can_only_see_their_private_annotations(self,
            search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        # Make a private annotation from a different user.
        Annotation(userid="acct:foo@auth2").id
        users_private_ids = [Annotation(userid=userid).id,
                             Annotation(userid=userid).id]

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(users_private_ids)

    def test_logged_in_user_can_see_shared_annotations(self,
            search, pyramid_config, Annotation):
        userid = "acct:bar@auth2"
        pyramid_config.testing_securitypolicy(userid)
        shared_ids = [Annotation(userid="acct:foo@auth2", shared=True).id,
                      Annotation(userid=userid, shared=True).id]

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(shared_ids)

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.AuthFilter(pyramid_request))
        return search


class TestGroupFilter(object):
    def test_matches_only_annotations_from_specified_group(self, search, Annotation, group):
        Annotation(groupid='group2')
        Annotation(groupid='group3')
        group1_annotations = [Annotation(groupid=group.pubid).id,
                              Annotation(groupid=group.pubid).id]

        result = search.run({'group': group.pubid})

        assert sorted(result.annotation_ids) == sorted(group1_annotations)

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.GroupFilter())
        return search

    @pytest.fixture
    def group(self, factories):
        return factories.OpenGroup(name="group1", pubid="group1id")


class TestGroupAuthFilter(object):
    def test_does_not_return_annotations_if_group_not_readable_by_user(
        self, search, Annotation, group_service
    ):
        group_service.groupids_readable_by.return_value = []
        Annotation(groupid="group2").id
        Annotation(groupid="group1").id
        Annotation(groupid="group1").id

        result = search.run({})

        assert not result.annotation_ids

    def test_returns_annotations_if_group_readable_by_user(
        self, search, Annotation, group_service
    ):
        group_service.groupids_readable_by.return_value = ["group1"]
        Annotation(groupid="group2", shared=True).id
        expected_ids = [Annotation(groupid="group1").id,
                        Annotation(groupid="group1").id]

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.GroupAuthFilter(pyramid_request))
        return search


class TestUserFilter(object):
    def test_filters_annotations_by_user(self, search, Annotation):
        Annotation(userid="acct:foo@auth2", shared=True)
        expected_ids = [Annotation(userid="acct:bar@auth2", shared=True).id]

        result = search.run({'user': "bar"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_annotations_by_multiple_users(self, search, Annotation):
        Annotation(userid="acct:foo@auth2", shared=True)
        expected_ids = [Annotation(userid="acct:bar@auth2", shared=True).id,
                        Annotation(userid="acct:baz@auth2", shared=True).id]

        params = webob.multidict.MultiDict()
        params.add("user", "bar")
        params.add("user", "baz")
        result = search.run(params)

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_annotations_by_user_and_authority(self, search, Annotation):
        Annotation(userid="acct:foo@auth2", shared=True)
        expected_ids = [Annotation(userid="acct:foo@auth3", shared=True).id]

        result = search.run({"user": "foo@auth3"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.UserFilter())
        return search


class TestUriFilter(object):
    @pytest.mark.parametrize("field", ("uri", "url"))
    def test_filters_by_field(self, search, Annotation, field):
        Annotation(target_uri="https://foo.com")
        expected_ids = [Annotation(target_uri="https://bar.com").id]

        result = search.run({field: "https://bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_on_whole_url(self, search, Annotation):
        Annotation(target_uri="http://bar.com/foo")
        expected_ids = [Annotation(target_uri="http://bar.com").id,
                        Annotation(target_uri="http://bar.com/").id]

        result = search.run({"url": "http://bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filter_matches_invalid_uri(self, search, Annotation):
        Annotation(target_uri="https://bar.com")
        expected_ids = [Annotation(target_uri="invalid-uri").id]

        result = search.run({"uri": "invalid-uri"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_filters_aliases_http_and_https(self, search, Annotation):
        expected_ids = [Annotation(target_uri="http://bar.com").id,
                        Annotation(target_uri="https://bar.com").id]

        result = search.run({"url": "http://bar.com"})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_returns_all_annotations_with_equivalent_uris(self, search, Annotation, storage):
        # Mark all these uri's as equivalent uri's.
        storage.expand_uri.side_effect = lambda _, x: [
            "urn:x-pdf:1234",
            "file:///Users/june/article.pdf",
            "doi:10.1.1/1234",
            "http://reading.com/x-pdf",
        ]
        Annotation(target_uri="urn:x-pdf:1235")
        Annotation(target_uri="file:///Users/jane/article.pdf").id
        expected_ids = [Annotation(target_uri="urn:x-pdf:1234").id,
                        Annotation(target_uri="doi:10.1.1/1234").id,
                        Annotation(target_uri="http://reading.com/x-pdf").id,
                        Annotation(target_uri="file:///Users/june/article.pdf").id]

        params = webob.multidict.MultiDict()
        params.add("url", "urn:x-pdf:1234")
        result = search.run(params)

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_ors_multiple_url_uris(self, search, Annotation):
        Annotation(target_uri="http://baz.com")
        Annotation(target_uri="https://www.foo.com")
        expected_ids = [Annotation(target_uri="https://bar.com").id,
                        Annotation(target_uri="http://bat.com").id,
                        Annotation(target_uri="http://foo.com").id,
                        Annotation(target_uri="https://foo.com/bar").id]

        params = webob.multidict.MultiDict()
        params.add("uri", "http://bat.com")
        params.add("uri", "https://bar.com")
        params.add("url", "http://foo.com")
        params.add("url", "https://foo.com/bar")
        result = search.run(params)

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    @pytest.fixture
    def search(self, search, pyramid_request):
        search.append_filter(query.UriFilter(pyramid_request))
        return search

    @pytest.fixture
    def storage(self, patch):
        return patch('h.search.query.storage')


class TestDeletedFilter(object):

    def test_excludes_deleted_annotations(self, search, Annotation):
        deleted_ids = [Annotation(deleted=True).id]
        not_deleted_ids = [Annotation(deleted=False).id]

        # Deleted annotations need to be marked in the index using `h.search.index.delete`.
        for id_ in deleted_ids:
            index.delete(search.es, id_, refresh=True)

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(not_deleted_ids)

    @pytest.fixture
    def search(self, search):
        search.append_filter(query.DeletedFilter())
        return search


@pytest.mark.usefixtures('pyramid_config')
class TestNipsaFilter(object):

    def test_hides_banned_users_annotations_from_other_users(
        self, pyramid_request, search, banned_user, user, Annotation
    ):
        pyramid_request.user = user
        search.append_filter(query.NipsaFilter(pyramid_request))
        Annotation(userid=banned_user.userid)
        expected_ids = [Annotation(userid=user.userid).id]

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_shows_banned_users_annotations_to_banned_user(
        self, pyramid_request, search, banned_user, user, Annotation
    ):
        pyramid_request.user = banned_user
        search.append_filter(query.NipsaFilter(pyramid_request))
        expected_ids = [Annotation(userid=banned_user.userid).id]

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    def test_shows_banned_users_annotations_in_groups_they_created(
        self, pyramid_request, search, banned_user, user, Annotation,
        group_service,
    ):
        pyramid_request.user = user
        group_service.groupids_created_by.return_value = ["created_by_banneduser"]
        search.append_filter(query.NipsaFilter(pyramid_request))
        expected_ids = [Annotation(groupid="created_by_banneduser",
                                   userid=banned_user.userid).id]

        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(expected_ids)

    @pytest.fixture
    def banned_user(self, factories):
        return factories.User(username="banned", nipsa=True)

    @pytest.fixture
    def user(self, factories):
        return factories.User(username="notbanned", nipsa=False)

    @pytest.fixture
    def pyramid_config(self, pyramid_config, banned_user):
        # Fake implementation of the `AnnotationTransformEvent` subscriber
        # which adds the "nipsa" flag to annotations during indexing.
        def add_nipsa_flag(event):
            if event.annotation.userid == banned_user.userid:
                event.annotation_dict['nipsa'] = True
        pyramid_config.add_subscriber(add_nipsa_flag, 'h.events.AnnotationTransformEvent')

        return pyramid_config

    @pytest.fixture
    def group_service(self, group_service):
        group_service.groupids_created_by.return_value = []
        return group_service


class TestAnyMatcher(object):
    def test_matches_uriparts(self, search, Annotation):
        Annotation(target_uri="http://bar.com")
        matched_ids = [Annotation(target_uri="http://foo.com").id,
                       Annotation(target_uri="http://foo.com/bar").id]

        result = search.run({"any": "foo"})

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    def test_matches_quote(self, search, Annotation):
        Annotation(target_selectors=[{'exact': 'selected bar text'}])
        matched_ids = [Annotation(target_selectors=[{'exact': 'selected foo text'}]).id,
                       Annotation(target_selectors=[{'exact': 'selected foo bar text'}]).id]

        result = search.run({"any": "foo"})

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    def test_matches_text(self, search, Annotation):
        Annotation(text="bar is best")
        matched_ids = [Annotation(text="foo is fun").id,
                       Annotation(text="foo is bar's friend").id]

        result = search.run({"any": "foo"})

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    def test_matches_tags(self, search, Annotation):
        Annotation(tags=["bar"])
        matched_ids = [Annotation(tags=["foo"]).id,
                       Annotation(tags=["foo", "bar"]).id]

        result = search.run({"any": "foo"})

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    def test_ors_any_matches(self, search, Annotation):
        """
        Any is expected to match any of the following fields;
        quote, text, uri.parts, and tags
        that contain any of the passed keywords.
        """
        Annotation(target_selectors=[{'exact': 'selected baz text'}])
        Annotation(tags=["baz"])
        Annotation(target_uri="baz.com")
        Annotation(text="baz is best")

        matched_ids = [Annotation(target_uri="foo/bar/baz.com").id,
                       Annotation(target_selectors=[{'exact': 'selected foo text'}]).id,
                       Annotation(text="bar is best").id,
                       Annotation(tags=["foo"]).id]

        params = webob.multidict.MultiDict()
        params.add("any", "foo")
        params.add("any", "bar")
        result = search.run(params)

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    @pytest.fixture
    def search(self, search):
        search.append_matcher(query.AnyMatcher())
        return search

    @pytest.fixture
    def Annotation(self, Annotation):
        # Override the default randomly-generated values for fields which
        # "any" matches against to ensure that we do not get unexpected
        # matches in tests. This will need to be modified if new fields are
        # added to the set which "any" matches against.
        def AnnotationWithDefaults(*args, **kwargs):
            kwargs.setdefault('tags', [])
            kwargs.setdefault('target_selectors', [{'exact': 'quotedoesnotmatch'}])
            kwargs.setdefault('target_uri', 'http://uridoesnotmatch.com')
            kwargs.setdefault('text', '')
            return Annotation(*args, **kwargs)
        return AnnotationWithDefaults


class TestTagsMatcher(object):
    def test_matches_tag_key(self, search, Annotation):
        Annotation(shared=True)
        Annotation(shared=True, tags=["bar"])
        matched_ids = [Annotation(shared=True, tags=["foo"]).id,
                       Annotation(shared=True, tags=["foo", "bar"]).id]

        result = search.run({"tag": "foo"})

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    def test_matches_tags_key(self, search, Annotation):
        Annotation(shared=True)
        Annotation(shared=True, tags=["bar"])
        matched_ids = [Annotation(shared=True, tags=["foo"]).id,
                       Annotation(shared=True, tags=["foo", "bar"]).id]

        result = search.run({"tags": "foo"})

        assert sorted(result.annotation_ids) == sorted(matched_ids)

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

        assert sorted(result.annotation_ids) == sorted(matched_ids)

    @pytest.fixture
    def search(self, search):
        search.append_matcher(query.TagsMatcher())
        return search


class TestRepliesMatcher(object):
    def test_matches_unnested_replies_to_annotations(self, Annotation, search):
        ann1 = Annotation()
        ann2 = Annotation()
        ann3 = Annotation()
        Annotation()
        # Create two replies on ann1.
        reply1 = Annotation(references=[ann1.id])
        reply2 = Annotation(references=[ann1.id])
        # Create a reply on ann2
        reply3 = Annotation(references=[ann2.id])
        # Create a reply on ann3
        Annotation(references=[ann3.id])

        expected_reply_ids = [reply1.id, reply2.id, reply3.id]

        ann_ids = [ann1.id, ann2.id]
        search.append_matcher(query.RepliesMatcher(ann_ids))
        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(expected_reply_ids)

    def test_matches_replies_of_replies_to_an_annotation(self, Annotation, search):
        ann1 = Annotation()
        # Create a reply on ann1 and a reply to the reply.
        reply1 = Annotation(references=[ann1.id])
        reply2 = Annotation(references=[ann1.id, reply1.id])

        expected_reply_ids = [reply1.id, reply2.id]

        ann_ids = [ann1.id]
        search.append_matcher(query.RepliesMatcher(ann_ids))
        result = search.run({})

        assert sorted(result.annotation_ids) == sorted(expected_reply_ids)


class TestTagsAggregation(object):
    def test_it_returns_annotation_counts_by_tag(self, Annotation, search):
        for i in range(2):
            Annotation(tags=["tag_a"])
        Annotation(tags=["tag_b"])

        search.append_aggregation(query.TagsAggregation())
        result = search.run({})

        tag_results = result.aggregations["tags"]
        count_for_tag_a = next(r for r in tag_results if r["tag"] == "tag_a")["count"]
        count_for_tag_b = next(r for r in tag_results if r["tag"] == "tag_b")["count"]

        assert len(tag_results) == 2
        assert count_for_tag_a == 2
        assert count_for_tag_b == 1

    def test_it_limits_number_of_annotation_counts_by_tag_returned(self, Annotation, search):
        bucket_limit = 2

        Annotation(tags=["tag_a"])
        for i in range(3):
            Annotation(tags=["tag_b"])
        for i in range(2):
            Annotation(tags=["tag_c"])

        search.append_aggregation(query.TagsAggregation(bucket_limit))
        result = search.run({})

        tag_results = result.aggregations["tags"]
        count_for_tag_b = next(r for r in tag_results if r["tag"] == "tag_b")["count"]
        count_for_tag_c = next(r for r in tag_results if r["tag"] == "tag_c")["count"]

        assert len(tag_results) == bucket_limit
        assert count_for_tag_b == 3
        assert count_for_tag_c == 2


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

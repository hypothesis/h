# -*- coding: utf-8 -*-

import datetime

import pytest
from mock import patch
from mock import PropertyMock

from pyramid import security

from h.api.models.elastic import Annotation, Document


class TestAnnotation(object):
    @pytest.mark.parametrize('annotation', [
        Annotation({'created': '2016-02-25T16:45:23.371848+00:00'}),
        Annotation({'created': '2016-02-25T16:45:23.371848'})])
    def test_created(self, annotation):
        assert annotation.created == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    @pytest.mark.parametrize('annotation', [
        Annotation({'created': 'invalid'}),
        Annotation({'created': ''}),
        Annotation({'created': None})])
    def test_created_invalid(self, annotation):
        assert annotation.created is None

    @pytest.mark.parametrize('annotation', [
        Annotation({'updated': '2016-02-25T16:45:23.371848+00:00'}),
        Annotation({'updated': '2016-02-25T16:45:23.371848'})])
    def test_updated(self, annotation):
        assert annotation.updated == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    @pytest.mark.parametrize('annotation', [
        Annotation({'updated': 'invalid'}),
        Annotation({'updated': ''}),
        Annotation({'updated': None})])
    def test_updated_invalid(self, annotation):
        assert annotation.updated is None

    def test_target_uri_from_uri(self):
        annotation = Annotation({'uri': 'http://example.com'})
        assert annotation.target_uri == 'http://example.com'

    @pytest.mark.parametrize('annotation', [
        Annotation({'uri': '', 'target': [{'source': 'http://example.com'}]}),
        Annotation({'target': [{'source': 'http://example.com'}]})])
    def test_target_uri_from_target_source(self, annotation):
        assert annotation.target_uri == 'http://example.com'

    def test_text(self):
        annotation = Annotation({'text': 'Lorem ipsum'})
        assert annotation.text == 'Lorem ipsum'

    @pytest.mark.parametrize('annotation', [
        Annotation({'text': ''}),
        Annotation({'text': None}),
        Annotation({})])
    def test_text_empty(self, annotation):
        assert annotation.text is None

    def test_tags(self):
        annotation = Annotation({'tags': ['foo', 'bar']})
        assert annotation.tags == ['foo', 'bar']

    def test_tags_string_type(self):
        annotation = Annotation({'tags': 'foo'})
        assert annotation.tags == ['foo']

    @pytest.mark.parametrize('annotation', [
        Annotation({'tags': []}),
        Annotation({'tags': None}),
        Annotation({})])
    def test_tags_empty(self, annotation):
        assert annotation.tags == []

    def test_userid(self):
        annotation = Annotation({'user': 'luke'})
        assert annotation.userid == 'luke'

    def test_groupid(self):
        annotation = Annotation({'group': '__world__'})
        assert annotation.groupid == '__world__'

    def test_references_allows_20_char_ids(self):
        annotation = Annotation({'references': ['AVMG6tocH9ZO4OKSk1WS']})
        assert annotation.references == ['AVMG6tocH9ZO4OKSk1WS']

    def test_references_allows_22_char_ids(self):
        annotation = Annotation({'references': ['AVMG6tocH9ZO4OKSk1WSaa']})
        assert annotation.references == ['AVMG6tocH9ZO4OKSk1WSaa']

    @pytest.mark.parametrize('annotation', [
        Annotation({'references': ['too short']}),
        Annotation({'references': ['this is way too long, it cannot be an id']})])
    def test_references_filters_out_non_ids(self, annotation):
        assert annotation.references == []

    @pytest.mark.parametrize('annotation', [
        Annotation({'permissions': {'read': ['group:__world__']}, 'user': 'luke', 'group': '__world__'}),
        Annotation({'permissions': {'read': ['group:tatooine']}, 'user': 'luke', 'group': 'tatooine'})])
    def test_shared_true(self, annotation):
        assert annotation.shared is True

    @pytest.mark.parametrize('annotation', [
        Annotation({'permissions': {'read': ['luke']}, 'user': 'luke', 'group': '__world__'}),
        Annotation({'permissions': {'read': ['luke']}, 'user': 'luke', 'group': 'tatooine'}),
        Annotation({'permissions': {'read': ['hansolo']}, 'user': 'luke', 'group': 'tatooine'})])
    def test_shared_false(self, annotation):
        assert annotation.shared is False

    def test_target_selectors(self):
        annotation = Annotation({'target': [{'selector': [{'foo': 'bar'}]}]})
        assert annotation.target_selectors == [{'foo': 'bar'}]

    def test_target_selectors_empty(self):
        annotation = Annotation({'target': {}})
        assert annotation.target_selectors == []

    def test_target_selectors_missing_target(self):
        annotation = Annotation({})
        assert annotation.target_selectors == []

    def test_extra(self):
        annotation = Annotation({
            'id': 'AVLBpz--vTW_3w8LyzKg',
            'created': '2016-02-08T16:11:49.576908+00:00',
            'updated': '2016-02-08T16:11:49.576908+00:00',
            'user': 'luke',
            'group': '__world__',
            'uri': 'https://example.com',
            'text': 'My comment',
            'tags': ['look'],
            'target': [{'source': 'https://example.com',
                        'selector': []}],
            'references': ['Qe7fpc5ZRgWy0RSHEP9UNg'],
            'permissions': {'read': ['group:__world__'],
                            'admin': ['luke'],
                            'update': ['luke'],
                            'delete': ['luke']},
            'document': {'title': 'Example'},
            'somethingelse': 'foo',
            'extra': {'foo': 'bar'}})
        assert annotation.extra == {'somethingelse': 'foo', 'extra': {'foo': 'bar'}}

    def test_extra_empty(self):
        annotation = Annotation({'id': 'Qe7fpc5ZRgWy0RSHEP9UNg'})
        assert annotation.extra is None

    def test_uri(self):
        assert Annotation(uri="http://foo.com").uri == "http://foo.com"

    def test_uri_with_no_uri(self):
        assert Annotation().uri == ""

    def test_uri_when_uri_is_not_a_string(self):
        for uri in (True, None, 23, 23.7, {"foo": False}, [1, 2, 3]):
            assert isinstance(Annotation(uri=uri).uri, unicode)

    def test_target_links_from_annotation(self):
        annotation = Annotation(target=[{'source': 'target link'}])
        assert annotation.target_links == ['target link']

    def test_parent_id_returns_none_if_no_references(self):
        annotation = Annotation()
        assert annotation.parent_id is None

    def test_parent_id_returns_none_if_empty_references(self):
        annotation = Annotation(references=[])
        assert annotation.parent_id is None

    def test_parent_id_returns_none_if_references_not_list(self):
        annotation = Annotation(references={'foo': 'bar'})
        assert annotation.parent_id is None

    def test_parent_id_returns_thread_parent_id(self):
        annotation = Annotation(references=['abc123', 'def456'])
        assert annotation.parent_id == 'def456'

    def test_document_returns_document_type(self):
        annotation = Annotation(document={'title': 'The title'})
        assert type(annotation.document) == Document

    def test_document_returns_none_without_document(self):
        annotation = Annotation()
        assert annotation.document is None

    def test_document_returns_none_with_empty_document(self):
        annotation = Annotation(document={})
        assert annotation.document is None

    @pytest.mark.parametrize('document', [
        'a string',
        [],
        [1, 2, 3],
        11,
        12.7])
    def test_document_returns_none_with_non_dict_document(self, document):
        annotation = Annotation(document=document)
        assert annotation.document is None

    def test_acl_principal(self):
        annotation = Annotation({
            'permissions': {
                'read': ['saoirse'],
            }
        })
        actual = annotation.__acl__()
        expect = [(security.Allow, 'saoirse', 'read'), security.DENY_ALL]
        assert actual == expect

    def test_acl_deny_system_role(self):
        annotation = Annotation({
            'permissions': {
                'read': [security.Everyone],
            }
        })
        actual = annotation.__acl__()
        expect = [security.DENY_ALL]
        assert actual == expect

    def test_acl_group(self):
        annotation = Annotation({
            'permissions': {
                'read': ['group:lulapalooza'],
            }
        })
        actual = annotation.__acl__()
        expect = [(security.Allow, 'group:lulapalooza', 'read'), security.DENY_ALL]
        assert actual == expect

    def test_acl_group_world(self):
        annotation = Annotation({
            'permissions': {
                'read': ['group:__world__'],
            }
        })
        actual = annotation.__acl__()
        expect = [(security.Allow, security.Everyone, 'read'), security.DENY_ALL]
        assert actual == expect

    @pytest.fixture
    def link_text(self, request):
        patcher = patch('h.api.models.elastic.Annotation.link_text',
                        new_callable=PropertyMock)
        request.addfinalizer(patcher.stop)
        return patcher.start()

    @pytest.fixture
    def title(self, request):
        patcher = patch('h.api.models.elastic.Annotation.title',
                        new_callable=PropertyMock)
        request.addfinalizer(patcher.stop)
        return patcher.start()

    @pytest.fixture
    def href(self, request):
        patcher = patch('h.api.models.elastic.Annotation.href',
                        new_callable=PropertyMock)
        request.addfinalizer(patcher.stop)
        return patcher.start()

    @pytest.fixture
    def hostname_or_filename(self, request):
        patcher = patch('h.api.models.elastic.Annotation.hostname_or_filename',
                        new_callable=PropertyMock)
        request.addfinalizer(patcher.stop)
        return patcher.start()

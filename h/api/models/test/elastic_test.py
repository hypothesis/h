# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import pytest
from mock import PropertyMock

from pyramid import security

from h.api.models.elastic import Annotation
from h.api.models.elastic import Document, DocumentMeta, DocumentURI


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
    def link_text(self, patch):
        return patch('h.api.models.elastic.Annotation.link_text',
                     autospec=None,
                     new_callable=PropertyMock)

    @pytest.fixture
    def title(self, patch):
        return patch('h.api.models.elastic.Annotation.title',
                     autospec=None,
                     new_callable=PropertyMock)

    @pytest.fixture
    def href(self, patch):
        return patch('h.api.models.elastic.Annotation.href',
                     autospec=None,
                     new_callable=PropertyMock)

    @pytest.fixture
    def hostname_or_filename(self, patch):
        return patch('h.api.models.elastic.Annotation.hostname_or_filename',
                     autospec=None,
                     new_callable=PropertyMock)


class TestDocument(object):
    def test_init(self):
        doc = Document({'foo': 'bar'})
        assert doc == {'foo': 'bar'}

    def test_init_claimant(self):
        doc = Document({}, claimant='http://example.com')
        assert doc.claimant == 'http://example.com'

    def test_init_created(self):
        doc = Document({}, created='created-value')
        assert doc.created == 'created-value'

    def test_init_updated(self):
        doc = Document({}, updated='updated-value')
        assert doc.updated == 'updated-value'

    def test_init_id(self):
        """It passes through other keyword arguments through to super class."""
        doc = Document({}, id='id-value')
        assert doc['id'] == 'id-value'

    def test_created(self):
        doc = Document({}, created=datetime.datetime(2016, 2, 25, 16, 45, 23, 371848))
        assert doc.created == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    def test_updated(self):
        doc = Document({}, updated=datetime.datetime(2016, 2, 25, 16, 45, 23, 371848))
        assert doc.updated == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    def test_title(self):
        doc = Document({'title': 'Example Page'})
        assert doc.title == 'Example Page'

    def test_title_array(self):
        doc = Document({'title': ['Example Page']})
        assert doc.title == 'Example Page'

    def test_title_empty_array(seld):
        doc = Document({'title': []})
        assert doc.title is None

    def test_meta(self):
        doc = Document({'og': {'title': ['Example Page'], 'url': ['http://example.com']},
                        'title': ['Example Page'],
                        'link': ['http://example.com', 'https://example.com']},
                       claimant='http://example.com',
                       created=datetime.datetime(2016, 2, 25, 16, 45, 23, 371848),
                       updated=datetime.datetime(2016, 2, 25, 16, 45, 23, 371849))

        expected = [DocumentMeta({'type': 'og.title', 'value': ['Example Page'],
                                  'claimant': 'http://example.com',
                                  'created': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848),
                                  'updated': datetime.datetime(2016, 2, 25, 16, 45, 23, 371849)}),

                    DocumentMeta({'type': 'og.url', 'value': ['http://example.com'],
                                  'claimant': 'http://example.com',
                                  'created': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848),
                                  'updated': datetime.datetime(2016, 2, 25, 16, 45, 23, 371849)}),

                    DocumentMeta({'type': 'title', 'value': ['Example Page'],
                                  'claimant': 'http://example.com',
                                  'created': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848),
                                  'updated': datetime.datetime(2016, 2, 25, 16, 45, 23, 371849)})]
        assert sorted(doc.meta) == sorted(expected)

    def test_uris_only_one_self_claim(self):
        doc = Document({'link': [{'href': 'http://example.com'}]},
                       claimant='http://example.com')

        expected = [DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'http://example.com',
                                 'type': 'self-claim',
                                 'created': None, 'updated': None})]

        assert doc.document_uris == expected

    def test_uris_discard_self_claim_when_claimant_is_missing(self):
        doc = Document({'link': [{'href': 'http://example.com'}]})
        expected = [DocumentURI({'claimant': None,
                                 'uri': 'http://example.com',
                                 'type': None,
                                 'content_type': None,
                                 'created': None, 'updated': None})]
        assert doc.document_uris == expected

    def test_uris_disregard_doi_links(self):
        doc = Document({'link': [{'href': 'doi:foobar'}]})
        assert len(doc.document_uris) == 0

    def test_uris_str_link(self):
        doc = Document({'link': 'http://example.com'},
                       claimant='http://example.com',
                       created=datetime.datetime(2016, 2, 25, 16, 45, 23, 371848),
                       updated=datetime.datetime(2016, 2, 25, 16, 45, 23, 371849))

        expected = [DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'http://example.com',
                                 'type': 'self-claim',
                                 'created': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848),
                                 'updated': datetime.datetime(2016, 2, 25, 16, 45, 23, 371849)})]

        assert doc.document_uris == expected

    def test_uris_recognize_highwire_pdf(self):
        doc = Document({'link': [{'href': 'pdf-uri', 'type': 'application/pdf'}]},
                       claimant='http://example.com')

        expected = [DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'pdf-uri',
                                 'type': 'highwire-pdf',
                                 'content_type': 'application/pdf',
                                 'created': None, 'updated': None}),

                    DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'http://example.com',
                                 'type': 'self-claim',
                                 'created': None, 'updated': None})]

        assert sorted(doc.document_uris) == sorted(expected)

    def test_uris_prefix_type_when_rel(self):
        doc = Document({'link': [{'href': 'https://example.com', 'rel': 'canonical'}]},
                       claimant='http://example.com')

        expected = [DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'https://example.com',
                                 'type': 'rel-canonical',
                                 'content_type': None,
                                 'created': None, 'updated': None}),

                    DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'http://example.com',
                                 'type': 'self-claim',
                                 'created': None, 'updated': None})]

        assert sorted(doc.document_uris) == sorted(expected)

    @pytest.mark.parametrize('doc', [
        Document({'highwire': {'doi': ['foobar']}}, claimant='http://example.com'),
        Document({'highwire': {'doi': ['doi:foobar']}}, claimant='http://example.com')])
    def test_uris_generates_doi_uri_from_highwire_meta(self, doc):
        expected = [DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'doi:foobar',
                                 'type': 'highwire-doi',
                                 'created': None, 'updated': None}),

                    DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'http://example.com',
                                 'type': 'self-claim',
                                 'created': None, 'updated': None})]

        assert sorted(doc.document_uris) == sorted(expected)

    @pytest.mark.parametrize('doc', [
        Document({'dc': {'identifier': ['foobar']}}, claimant='http://example.com'),
        Document({'dc': {'identifier': ['doi:foobar']}}, claimant='http://example.com')])
    def test_uris_generates_doi_uri_from_dc_meta(self, doc):
        expected = [DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'doi:foobar',
                                 'type': 'dc-doi',
                                 'created': None, 'updated': None}),

                    DocumentURI({'claimant': 'http://example.com',
                                 'uri': 'http://example.com',
                                 'type': 'self-claim',
                                 'created': None, 'updated': None})]

        assert sorted(doc.document_uris) == sorted(expected)


class TestDocumentMeta(object):
    def test_created(self):
        meta = DocumentMeta({'created': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)})
        assert meta.created == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    def test_updated(self):
        meta = DocumentMeta({'updated': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)})
        assert meta.updated == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    def test_claimant(self):
        meta = DocumentMeta({'claimant': 'http://example.com'})
        assert meta.claimant == 'http://example.com'

    def test_claimant_normalized(self):
        meta = DocumentMeta({'claimant': 'http://example.com/'})
        assert meta.claimant_normalized == 'http://example.com'

    def test_type(self):
        meta = DocumentMeta({'type': 'title'})
        assert meta.type == 'title'

    @pytest.mark.parametrize('type', ['oga.title', 'dc.og.title'])
    def test_type_skips_og_normalisation(self, type):
        meta = DocumentMeta({'type': type})
        assert meta.type == type

    def test_value(self):
        meta = DocumentMeta({'value': 'Example Page'})
        assert meta.value == 'Example Page'

    def test_normalized_type_normalizes_multiple_dots(self):
        meta = DocumentMeta({'type': 'dc..description'})
        assert meta.normalized_type == 'dc.description'

    def test_normalized_type_normalizes_case(self):
        meta = DocumentMeta({'type': 'dc.Contributor.Sponsor'})
        assert meta.normalized_type == 'dc.contributor.sponsor'

    def test_normalized_type_normalizes_colons(self):
        meta = DocumentMeta({'type': 'facebook.book:isbn'})
        assert meta.normalized_type == 'facebook.book.isbn'

    def test_normalized_type_normalizes_og(self):
        meta = DocumentMeta({'type': 'og.title'})
        assert meta.normalized_type == 'facebook.title'


class TestDocumentURI(object):
    def test_created(self):
        docuri = DocumentURI({'created': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)})
        assert docuri.created == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    def test_updated(self):
        docuri = DocumentURI({'updated': datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)})
        assert docuri.updated == datetime.datetime(2016, 2, 25, 16, 45, 23, 371848)

    def test_claimant(self):
        docuri = DocumentURI({'claimant': 'http://example.com'})
        assert docuri.claimant == 'http://example.com'

    def test_claimant_normalized(self):
        docuri = DocumentURI({'claimant': 'http://example.com/'})
        assert docuri.claimant_normalized == 'http://example.com'

    def test_uri(self):
        docuri = DocumentURI({'uri': 'http://example.com'})
        assert docuri.uri == 'http://example.com'

    def test_uri_normalized(self):
        docuri = DocumentURI({'uri': 'http://example.com/'})
        assert docuri.uri_normalized == 'http://example.com'

    def test_type(self):
        docuri = DocumentURI({'type': 'rel-canonical'})
        assert docuri.type == 'rel-canonical'

    def test_content_type(self):
        docuri = DocumentURI({'content_type': 'application/pdf'})
        assert docuri.content_type == 'application/pdf'

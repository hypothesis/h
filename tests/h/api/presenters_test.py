# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import mock
import pytest

from h.api import models
from h.api.presenters import AnnotationBasePresenter
from h.api.presenters import AnnotationJSONPresenter
from h.api.presenters import AnnotationSearchIndexPresenter
from h.api.presenters import AnnotationJSONLDPresenter
from h.api.presenters import DocumentJSONPresenter
from h.api.presenters import DocumentMetaJSONPresenter
from h.api.presenters import DocumentURIJSONPresenter
from h.api.presenters import add_annotation_link_generator
from h.api.presenters import utc_iso8601, deep_merge_dict


@pytest.mark.usefixtures('routes')
class TestAnnotationBasePresenter(object):

    def test_constructor_args(self, pyramid_request):
        annotation = mock.Mock()

        presenter = AnnotationBasePresenter(pyramid_request, annotation)

        assert presenter.request == pyramid_request
        assert presenter.annotation == annotation

    def test_created_returns_none_if_missing(self, pyramid_request):
        annotation = mock.Mock(created=None)

        created = AnnotationBasePresenter(pyramid_request, annotation).created

        assert created is None

    def test_created_uses_iso_format(self, pyramid_request):
        when = datetime.datetime(2012, 3, 14, 23, 34, 47, 12)
        annotation = mock.Mock(created=when)

        created = AnnotationBasePresenter(pyramid_request, annotation).created

        assert created == '2012-03-14T23:34:47.000012+00:00'

    def test_updated_returns_none_if_missing(self, pyramid_request):
        annotation = mock.Mock(updated=None)

        updated = AnnotationBasePresenter(pyramid_request, annotation).updated

        assert updated is None

    def test_updated_uses_iso_format(self, pyramid_request):
        when = datetime.datetime(1983, 8, 31, 7, 18, 20, 98763)
        annotation = mock.Mock(updated=when)

        updated = AnnotationBasePresenter(pyramid_request, annotation).updated

        assert updated == '1983-08-31T07:18:20.098763+00:00'

    def test_links_empty(self, pyramid_request):
        annotation = mock.Mock()

        links = AnnotationBasePresenter(pyramid_request, annotation).links

        assert links == {}

    def test_links_includes_registered_links(self, pyramid_request):
        annotation = mock.Mock()
        add_annotation_link_generator(pyramid_request.registry,
                                      'giraffe',
                                      lambda r, a: 'http://foo.com/bar/123')

        links = AnnotationBasePresenter(pyramid_request, annotation).links

        assert links == {
            'giraffe': 'http://foo.com/bar/123'
        }

    def test_links_omits_link_generators_that_return_none(self, pyramid_request):
        annotation = mock.Mock()
        add_annotation_link_generator(pyramid_request.registry,
                                      'giraffe',
                                      lambda r, a: 'http://foo.com/bar/123')
        add_annotation_link_generator(pyramid_request.registry,
                                      'donkey',
                                      lambda r, a: None)

        links = AnnotationBasePresenter(pyramid_request, annotation).links

        assert links == {
            'giraffe': 'http://foo.com/bar/123'
        }

    def test_link_generators_called_with_pyramid_request_and_annotation(self, pyramid_request):
        annotation = mock.Mock()
        dummy_link_generator = mock.Mock(return_value='')
        add_annotation_link_generator(pyramid_request.registry,
                                      'giraffe',
                                      dummy_link_generator)

        links = AnnotationBasePresenter(pyramid_request, annotation).links

        dummy_link_generator.assert_called_once_with(pyramid_request, annotation)

    def test_text(self, pyramid_request):
        ann = mock.Mock(text='It is magical!')
        presenter = AnnotationBasePresenter(pyramid_request, ann)

        assert 'It is magical!' == presenter.text

    def test_text_missing(self, pyramid_request):
        ann = mock.Mock(text=None)
        presenter = AnnotationBasePresenter(pyramid_request, ann)

        assert '' == presenter.text

    def test_tags(self, pyramid_request):
        ann = mock.Mock(tags=['interesting', 'magic'])
        presenter = AnnotationBasePresenter(pyramid_request, ann)

        assert ['interesting', 'magic'] == presenter.tags

    def test_tags_missing(self, pyramid_request):
        ann = mock.Mock(tags=None)
        presenter = AnnotationBasePresenter(pyramid_request, ann)

        assert [] == presenter.tags

    def test_target(self, pyramid_request):
        ann = mock.Mock(target_uri='http://example.com',
                        target_selectors={'PositionSelector': {'start': 0, 'end': 12}})

        expected = [{'source': 'http://example.com', 'selector': {'PositionSelector': {'start': 0, 'end': 12}}}]
        actual = AnnotationJSONPresenter(pyramid_request, ann).target
        assert expected == actual

    def test_target_missing_selectors(self, pyramid_request):
        ann = mock.Mock(target_uri='http://example.com',
                        target_selectors=None)

        expected = [{'source': 'http://example.com'}]
        actual = AnnotationJSONPresenter(pyramid_request, ann).target
        assert expected == actual

    @pytest.fixture
    def routes(self, config):
        config.add_route('api.annotation', '/dummy/:id')



class TestAnnotationJSONPresenter(object):
    def test_asdict(self, document_asdict, pyramid_request):
        ann = mock.Mock(id='the-id',
                        created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
                        updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
                        userid='acct:luke',
                        target_uri='http://example.com',
                        text='It is magical!',
                        tags=['magic'],
                        groupid='__world__',
                        shared=True,
                        target_selectors=[{'TestSelector': 'foobar'}],
                        references=['referenced-id-1', 'referenced-id-2'],
                        extra={'extra-1': 'foo', 'extra-2': 'bar'})

        document_asdict.return_value = {'foo': 'bar'}

        expected = {'id': 'the-id',
                    'created': '2016-02-24T18:03:25.000768+00:00',
                    'updated': '2016-02-29T10:24:05.000564+00:00',
                    'user': 'acct:luke',
                    'uri': 'http://example.com',
                    'text': 'It is magical!',
                    'tags': ['magic'],
                    'group': '__world__',
                    'permissions': {'read': ['group:__world__'],
                                    'admin': ['acct:luke'],
                                    'update': ['acct:luke'],
                                    'delete': ['acct:luke']},
                    'target': [{'source': 'http://example.com',
                                'selector': [{'TestSelector': 'foobar'}]}],
                    'document': {'foo': 'bar'},
                    'links': {},
                    'references': ['referenced-id-1', 'referenced-id-2'],
                    'extra-1': 'foo',
                    'extra-2': 'bar'}

        result = AnnotationJSONPresenter(pyramid_request, ann).asdict()

        assert result == expected

    def test_asdict_extra_cannot_override_other_data(self, document_asdict, pyramid_request):
        ann = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(pyramid_request, ann).asdict()
        assert presented['id'] == 'the-real-id'

    def test_asdict_extra_uses_copy_of_extra(self, document_asdict, pyramid_request):
        extra = {'foo': 'bar'}
        ann = mock.Mock(id='my-id', extra=extra)
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(pyramid_request, ann).asdict()

        # Presenting the annotation shouldn't change the "extra" dict.
        assert extra == {'foo': 'bar'}

    def test_asdict_with_link_generators(self, document_asdict, pyramid_request):
        ann = mock.Mock(id='my-id', extra={})
        document_asdict.return_value = {}

        add_annotation_link_generator(pyramid_request.registry,
                                      'giraffe',
                                      lambda r, a: 'http://giraffe.com')
        add_annotation_link_generator(pyramid_request.registry,
                                      'withid',
                                      lambda r, a: 'http://withid.com/' + a.id)

        presented = AnnotationJSONPresenter(pyramid_request, ann).asdict()

        assert presented['links'] == {
            'giraffe': 'http://giraffe.com',
            'withid': 'http://withid.com/my-id',
        }

    @pytest.mark.parametrize('annotation,action,expected', [
        (mock.Mock(userid='acct:luke', shared=False), 'read', ['acct:luke']),
        (mock.Mock(groupid='__world__', shared=True), 'read', ['group:__world__']),
        (mock.Mock(groupid='lulapalooza', shared=True), 'read', ['group:lulapalooza']),
        (mock.Mock(userid='acct:luke'), 'admin', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'update', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'delete', ['acct:luke']),
        ])
    def test_permissions(self, annotation, action, expected, pyramid_request):
        presenter = AnnotationJSONPresenter(pyramid_request, annotation)
        assert expected == presenter.permissions[action]

    @pytest.fixture
    def document_asdict(self, patch):
        return patch('h.api.presenters.DocumentJSONPresenter.asdict')


@pytest.mark.usefixtures('DocumentJSONPresenter')
class TestAnnotationSearchIndexPresenter(object):

    def test_asdict(self, DocumentJSONPresenter, pyramid_request):
        annotation = mock.Mock(
            id='xyz123',
            created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
            updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
            userid='acct:luke@hypothes.is',
            target_uri='http://example.com',
            target_uri_normalized='http://example.com/normalized',
            text='It is magical!',
            tags=['magic'],
            groupid='__world__',
            shared=True,
            target_selectors=[{'TestSelector': 'foobar'}],
            references=['referenced-id-1', 'referenced-id-2'],
            extra={'extra-1': 'foo', 'extra-2': 'bar'})
        DocumentJSONPresenter.return_value.asdict.return_value = {'foo': 'bar'}

        annotation_dict = AnnotationSearchIndexPresenter(
            pyramid_request, annotation).asdict()

        assert annotation_dict == {
            'id': 'xyz123',
            'created': '2016-02-24T18:03:25.000768+00:00',
            'updated': '2016-02-29T10:24:05.000564+00:00',
            'user': 'acct:luke@hypothes.is',
            'uri': 'http://example.com',
            'text': 'It is magical!',
            'tags': ['magic'],
            'group': '__world__',
            'permissions': {'read': ['group:__world__'],
                            'admin': ['acct:luke@hypothes.is'],
                            'update': ['acct:luke@hypothes.is'],
                            'delete': ['acct:luke@hypothes.is']},
            'target': [{'scope': ['http://example.com/normalized'],
                        'source': 'http://example.com',
                        'selector': [{'TestSelector': 'foobar'}]}],
            'document': {'foo': 'bar'},
            'references': ['referenced-id-1', 'referenced-id-2'],
            'extra-1': 'foo',
            'extra-2': 'bar',
        }

    def test_asdict_extra_cannot_override_other_data(self, pyramid_request):
        annotation = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})

        annotation_dict = AnnotationSearchIndexPresenter(
            pyramid_request, annotation).asdict()

        assert annotation_dict['id'] == 'the-real-id'

    def test_asdict_does_not_modify_extra(self, pyramid_request):
        extra = {'foo': 'bar'}
        annotation = mock.Mock(id='my-id', extra=extra)

        AnnotationSearchIndexPresenter(pyramid_request, annotation).asdict()

        assert extra == {'foo': 'bar'}, (
                "Presenting the annotation shouldn't change the 'extra' dict")

    def test_asdict_does_not_return_links_from_link_generators(self, pyramid_request):
        annotation = mock.Mock(id='my-id', extra={})
        add_annotation_link_generator(pyramid_request.registry,
                                      'giraffe',
                                      lambda r, a: 'http://giraffe.com')
        add_annotation_link_generator(pyramid_request.registry,
                                      'withid',
                                      lambda r, a: 'http://withid.com/' + a.id)

        annotation_dict = AnnotationSearchIndexPresenter(
            pyramid_request, annotation).asdict()

        assert 'links' not in annotation_dict

    @pytest.mark.parametrize('annotation,action,expected', [
        (mock.Mock(userid='acct:luke', shared=False), 'read', ['acct:luke']),
        (mock.Mock(groupid='__world__', shared=True), 'read',
            ['group:__world__']),
        (mock.Mock(groupid='lulapalooza', shared=True), 'read',
            ['group:lulapalooza']),
        (mock.Mock(userid='acct:luke'), 'admin', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'update', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'delete', ['acct:luke']),
        ])
    def test_permissions(self, annotation, action, expected, pyramid_request):
        presenter = AnnotationSearchIndexPresenter(pyramid_request, annotation)

        assert expected == presenter.permissions[action]

    def test_it_copies_target_uri_normalized_to_target_scope(self, pyramid_request):
        annotation = mock.Mock(
            target_uri_normalized='http://example.com/normalized',
            extra={})

        annotation_dict = AnnotationSearchIndexPresenter(
            pyramid_request, annotation).asdict()

        assert annotation_dict['target'][0]['scope'] == [
            'http://example.com/normalized']

    @pytest.fixture
    def DocumentJSONPresenter(self, patch):
        class_ = patch('h.api.presenters.DocumentJSONPresenter')
        class_.return_value.asdict.return_value = {}
        return class_


@pytest.mark.usefixtures('routes')
class TestAnnotationJSONLDPresenter(object):

    def test_asdict(self, pyramid_request):
        annotation = mock.Mock(
            id='foobar',
            created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
            updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
            userid='acct:luke',
            target_uri='http://example.com',
            text='It is magical!',
            tags=['magic'],
            target_selectors=[{'TestSelector': 'foobar'}])
        expected = {
            '@context': 'http://www.w3.org/ns/anno.jsonld',
            'type': 'Annotation',
            'id': 'http://example.com/ann/foobar',
            'created': '2016-02-24T18:03:25.000768+00:00',
            'modified': '2016-02-29T10:24:05.000564+00:00',
            'creator': 'acct:luke',
            'body': [{'type': 'TextualBody',
                      'format': 'text/markdown',
                      'text': 'It is magical!'},
                     {'type': 'TextualBody',
                      'purpose': 'tagging',
                      'text': 'magic'}],
            'target': [{'source': 'http://example.com',
                        'selector': [{'TestSelector': 'foobar'}]}]
        }

        result = AnnotationJSONLDPresenter(pyramid_request, annotation).asdict()

        assert result == expected

    def test_id_returns_annotation_url(self, pyramid_request):
        annotation = mock.Mock(id='foobar')

        presenter = AnnotationJSONLDPresenter(pyramid_request, annotation)

        assert presenter.id == 'http://example.com/ann/foobar'

    def test_bodies_returns_textual_body(self, pyramid_request):
        annotation = mock.Mock(text='Flib flob flab', tags=None)

        bodies = AnnotationJSONLDPresenter(pyramid_request, annotation).bodies

        assert bodies == [{
            'type': 'TextualBody',
            'text': 'Flib flob flab',
            'format': 'text/markdown',
        }]

    def test_bodies_appends_tag_bodies(self, pyramid_request):
        annotation = mock.Mock(text='Flib flob flab', tags=['giraffe', 'lion'])

        bodies = AnnotationJSONLDPresenter(pyramid_request, annotation).bodies

        assert {
            'type': 'TextualBody',
            'text': 'giraffe',
            'purpose': 'tagging',
        } in bodies
        assert {
            'type': 'TextualBody',
            'text': 'lion',
            'purpose': 'tagging',
        } in bodies

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('annotation', '/ann/{id}')


class TestDocumentJSONPresenter(object):
    def test_asdict(self, db_session):
        document = models.Document(
            document_uris=[models.DocumentURI(uri='http://foo.com', claimant='http://foo.com'),
                           models.DocumentURI(uri='http://foo.org', claimant='http://foo.com', type='rel-canonical')],
            meta=[models.DocumentMeta(type='title', value=['Foo'], claimant='http://foo.com')])
        db_session.add(document)
        db_session.flush()

        presenter = DocumentJSONPresenter(document)
        expected = {'link': [{'href': 'http://foo.com'},
                             {'href': 'http://foo.org', 'rel': 'canonical'}],
                    'title': ['Foo']}
        assert expected == presenter.asdict()

    def test_asdict_when_none_document(self):
        assert {} == DocumentJSONPresenter(None).asdict()

    def test_asdict_does_not_render_other_meta_than_title(self, db_session):
        document = models.Document(meta=[
            models.DocumentMeta(type='title', value=['Foo'], claimant='http://foo.com'),
            models.DocumentMeta(type='twitter.url', value=['http://foo.com'], claimant='http://foo.com'),
            models.DocumentMeta(type='facebook.title', value=['FB Title'], claimant='http://foo.com'),
        ])
        db_session.add(document)
        db_session.flush()

        presenter = DocumentJSONPresenter(document)
        assert {'link': [], 'title': ['Foo']} == presenter.asdict()


class TestDocumentMetaJSONPresenter(object):
    def test_asdict(self):
        meta = mock.Mock(type='twitter.url.main_url',
                         value='https://example.com')
        presenter = DocumentMetaJSONPresenter(meta)

        expected = {'twitter': {'url': {'main_url': 'https://example.com'}}}
        assert expected == presenter.asdict()


class TestDocumentURIJSONPresenter(object):
    def test_asdict(self):
        docuri = mock.Mock(uri='http://example.com/site.pdf',
                           type='rel-alternate',
                           content_type='application/pdf')
        presenter = DocumentURIJSONPresenter(docuri)

        expected = {'href': 'http://example.com/site.pdf',
                    'rel': 'alternate',
                    'type': 'application/pdf'}

        assert expected == presenter.asdict()

    def test_asdict_empty_rel(self):
        docuri = mock.Mock(uri='http://example.com',
                           type='dc-doi',
                           content_type='text/html')
        presenter = DocumentURIJSONPresenter(docuri)

        expected = {'href': 'http://example.com', 'type': 'text/html'}

        assert expected == presenter.asdict()

    def test_asdict_empty_type(self):
        docuri = mock.Mock(uri='http://example.com',
                           type='rel-canonical',
                           content_type=None)
        presenter = DocumentURIJSONPresenter(docuri)

        expected = {'href': 'http://example.com', 'rel': 'canonical'}

        assert expected == presenter.asdict()

    def test_rel_with_type_rel(self):
        docuri = mock.Mock(type='rel-canonical')
        presenter = DocumentURIJSONPresenter(docuri)
        assert 'canonical' == presenter.rel

    def test_rel_with_non_rel_type(self):
        docuri = mock.Mock(type='highwire-pdf')
        presenter = DocumentURIJSONPresenter(docuri)
        assert presenter.rel is None


def test_utc_iso8601():
    t = datetime.datetime(2016, 2, 24, 18, 03, 25, 7685)
    assert utc_iso8601(t) == '2016-02-24T18:03:25.007685+00:00'


def test_utc_iso8601_ignores_timezone():
    t = datetime.datetime(2016, 2, 24, 18, 03, 25, 7685, Berlin())
    assert utc_iso8601(t) == '2016-02-24T18:03:25.007685+00:00'


def test_deep_merge_dict():
    a = {'foo': 1, 'bar': 2, 'baz': {'foo': 3, 'bar': 4}}
    b = {'bar': 8, 'baz': {'bar': 6, 'qux': 7}, 'qux': 15}
    deep_merge_dict(a, b)

    assert a == {
        'foo': 1,
        'bar': 8,
        'baz': {
            'foo': 3,
            'bar': 6,
            'qux': 7},
        'qux': 15}


class Berlin(datetime.tzinfo):
    """Berlin timezone, without DST support"""

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1)

    def tzname(self, dt):
        return "Berlin"

    def dst(self, dt):
        return datetime.timedelta()

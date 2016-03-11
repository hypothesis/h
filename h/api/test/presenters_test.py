# -*- coding: utf-8 -*-

import datetime
import mock
import pytest
from pyramid.testing import DummyRequest

from h.api.presenters import AnnotationBasePresenter
from h.api.presenters import AnnotationJSONPresenter
from h.api.presenters import DocumentJSONPresenter
from h.api.presenters import DocumentMetaJSONPresenter
from h.api.presenters import DocumentURIJSONPresenter
from h.api.presenters import add_annotation_link_generator
from h.api.presenters import utc_iso8601, deep_merge_dict


class TestAnnotationBasePresenter(object):

    @pytest.fixture(autouse=True)
    def link_routes(self, routes_mapper):
        routes_mapper.add_route('api.annotation', '/dummy/abc123')

    def test_constructor_args(self):
        request = DummyRequest()
        annotation = mock.Mock()

        presenter = AnnotationBasePresenter(request, annotation)

        assert presenter.request == request
        assert presenter.annotation == annotation

    def test_links_empty(self):
        request = DummyRequest()
        annotation = mock.Mock()

        links = AnnotationBasePresenter(request, annotation).links

        assert links == {}

    def test_links_includes_registered_links(self):
        request = DummyRequest()
        annotation = mock.Mock()
        dummy_link_generator = mock.Mock()
        dummy_link_generator.return_value = 'http://foo.com/bar/123'

        add_annotation_link_generator(request.registry,
                                      'giraffe',
                                      dummy_link_generator)

        links = AnnotationBasePresenter(request, annotation).links

        assert links == {
            'giraffe': 'http://foo.com/bar/123'
        }

    def test_link_generators_called_with_request_and_annotation(self):
        request = DummyRequest()
        annotation = mock.Mock()
        dummy_link_generator = mock.Mock(return_value='')

        add_annotation_link_generator(request.registry,
                                      'giraffe',
                                      dummy_link_generator)

        links = AnnotationBasePresenter(request, annotation).links

        dummy_link_generator.assert_called_once_with(request, annotation)


class TestAnnotationJSONPresenter(object):
    def test_asdict(self, document_asdict):
        request = DummyRequest()
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

        result = AnnotationJSONPresenter(request, ann).asdict()

        assert result == expected

    def test_asdict_extra_cannot_override_other_data(self, document_asdict):
        request = DummyRequest()
        ann = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(request, ann).asdict()
        assert presented['id'] == 'the-real-id'

    def test_asdict_extra_uses_copy_of_extra(self, document_asdict):
        extra = {'foo': 'bar'}
        request = DummyRequest()
        ann = mock.Mock(id='my-id', extra=extra)
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(request, ann).asdict()

        # Presenting the annotation shouldn't change the "extra" dict.
        assert extra == {'foo': 'bar'}

    def test_asdict_with_link_generators(self, document_asdict):
        request = DummyRequest()
        ann = mock.Mock(id='my-id', extra={})
        document_asdict.return_value = {}

        add_annotation_link_generator(request.registry,
                                      'giraffe',
                                      lambda r, a: 'http://giraffe.com')
        add_annotation_link_generator(request.registry,
                                      'withid',
                                      lambda r, a: 'http://withid.com/' + a.id)

        presented = AnnotationJSONPresenter(request, ann).asdict()

        assert presented['links'] == {
            'giraffe': 'http://giraffe.com',
            'withid': 'http://withid.com/my-id',
        }

    def test_text(self):
        request = DummyRequest()
        ann = mock.Mock(text='It is magical!')
        presenter = AnnotationJSONPresenter(request, ann)

        assert 'It is magical!' == presenter.text

    def test_text_missing(self):
        request = DummyRequest()
        ann = mock.Mock(text=None)
        presenter = AnnotationJSONPresenter(request, ann)

        assert '' == presenter.text

    def test_tags(self):
        request = DummyRequest()
        ann = mock.Mock(tags=['interesting', 'magic'])
        presenter = AnnotationJSONPresenter(request, ann)

        assert ['interesting', 'magic'] == presenter.tags

    def test_tags_missing(self):
        request = DummyRequest()
        ann = mock.Mock(tags=None)
        presenter = AnnotationJSONPresenter(request, ann)

        assert [] == presenter.tags

    @pytest.mark.parametrize('annotation,action,expected', [
        (mock.Mock(userid='acct:luke', shared=False), 'read', ['acct:luke']),
        (mock.Mock(groupid='__world__', shared=True), 'read', ['group:__world__']),
        (mock.Mock(groupid='lulapalooza', shared=True), 'read', ['group:lulapalooza']),
        (mock.Mock(userid='acct:luke'), 'admin', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'update', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'delete', ['acct:luke']),
        ])
    def test_permissions(self, annotation, action, expected):
        request = DummyRequest()
        presenter = AnnotationJSONPresenter(request, annotation)
        assert expected == presenter.permissions[action]

    def test_target(self):
        request = DummyRequest()
        ann = mock.Mock(target_uri='http://example.com',
                        target_selectors={'PositionSelector': {'start': 0, 'end': 12}})

        expected = [{'source': 'http://example.com', 'selector': {'PositionSelector': {'start': 0, 'end': 12}}}]
        actual = AnnotationJSONPresenter(request, ann).target
        assert expected == actual

    def test_target_missing_selectors(self):
        request = DummyRequest()
        ann = mock.Mock(target_uri='http://example.com',
                        target_selectors=None)

        expected = [{'source': 'http://example.com'}]
        actual = AnnotationJSONPresenter(request, ann).target
        assert expected == actual

    @pytest.fixture
    def document_asdict(self, request):
        patcher = mock.patch('h.api.presenters.DocumentJSONPresenter.asdict',
                             autospec=True)
        method = patcher.start()
        request.addfinalizer(patcher.stop)
        return method


class TestDocumentJSONPresenter(object):
    def test_asdict(self):
        document = mock.Mock(document_uris=[mock.Mock(uri='http://foo.com', type=None, content_type=None),
                                            mock.Mock(uri='http://foo.org', type='rel-canonical', content_type=None)],
                             meta=[mock.Mock(type='twitter.url.main_url', value='http://foo.org'),
                                   mock.Mock(type='twitter.title', value='Foo')])
        presenter = DocumentJSONPresenter(document)

        expected = {'link': [{'href': 'http://foo.com'},
                             {'href': 'http://foo.org', 'rel': 'canonical'}],
                    'twitter': {'title': 'Foo', 'url': {'main_url': 'http://foo.org'}}}
        assert expected == presenter.asdict()

    def test_asdict_when_none_document(self):
        assert {} == DocumentJSONPresenter(None).asdict()


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

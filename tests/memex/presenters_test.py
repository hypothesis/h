# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import mock
import pytest

from memex import models
from memex.presenters import AnnotationBasePresenter
from memex.presenters import AnnotationJSONPresenter
from memex.presenters import AnnotationSearchIndexPresenter
from memex.presenters import AnnotationJSONLDPresenter
from memex.presenters import DocumentJSONPresenter
from memex.presenters import utc_iso8601, deep_merge_dict


class TestAnnotationBasePresenter(object):

    def test_constructor_args(self, fake_links_service):
        annotation = mock.Mock()

        presenter = AnnotationBasePresenter(annotation, fake_links_service)

        assert presenter.annotation == annotation

    def test_created_returns_none_if_missing(self, fake_links_service):
        annotation = mock.Mock(created=None)

        created = AnnotationBasePresenter(annotation, fake_links_service).created

        assert created is None

    def test_created_uses_iso_format(self, fake_links_service):
        when = datetime.datetime(2012, 3, 14, 23, 34, 47, 12)
        annotation = mock.Mock(created=when)

        created = AnnotationBasePresenter(annotation, fake_links_service).created

        assert created == '2012-03-14T23:34:47.000012+00:00'

    def test_updated_returns_none_if_missing(self, fake_links_service):
        annotation = mock.Mock(updated=None)

        updated = AnnotationBasePresenter(annotation, fake_links_service).updated

        assert updated is None

    def test_updated_uses_iso_format(self, fake_links_service):
        when = datetime.datetime(1983, 8, 31, 7, 18, 20, 98763)
        annotation = mock.Mock(updated=when)

        updated = AnnotationBasePresenter(annotation, fake_links_service).updated

        assert updated == '1983-08-31T07:18:20.098763+00:00'

    def test_links(self, fake_links_service):
        annotation = mock.Mock()

        links = AnnotationBasePresenter(annotation, fake_links_service).links

        assert links == {'giraffe': 'http://giraffe.com',
                         'toad': 'http://toad.net'}

    def test_links_passes_annotation(self, fake_links_service):
        annotation = mock.Mock()

        links = AnnotationBasePresenter(annotation, fake_links_service).links

        assert fake_links_service.last_annotation == annotation

    def test_text(self, fake_links_service):
        ann = mock.Mock(text='It is magical!')
        presenter = AnnotationBasePresenter(ann, fake_links_service)

        assert 'It is magical!' == presenter.text

    def test_text_missing(self, fake_links_service):
        ann = mock.Mock(text=None)
        presenter = AnnotationBasePresenter(ann, fake_links_service)

        assert '' == presenter.text

    def test_tags(self, fake_links_service):
        ann = mock.Mock(tags=['interesting', 'magic'])
        presenter = AnnotationBasePresenter(ann, fake_links_service)

        assert ['interesting', 'magic'] == presenter.tags

    def test_tags_missing(self, fake_links_service):
        ann = mock.Mock(tags=None)
        presenter = AnnotationBasePresenter(ann, fake_links_service)

        assert [] == presenter.tags

    def test_target(self, fake_links_service):
        ann = mock.Mock(target_uri='http://example.com',
                        target_selectors={'PositionSelector': {'start': 0, 'end': 12}})

        expected = [{'source': 'http://example.com', 'selector': {'PositionSelector': {'start': 0, 'end': 12}}}]
        actual = AnnotationBasePresenter(ann, fake_links_service).target
        assert expected == actual

    def test_target_missing_selectors(self, fake_links_service):
        ann = mock.Mock(target_uri='http://example.com',
                        target_selectors=None)

        expected = [{'source': 'http://example.com'}]
        actual = AnnotationBasePresenter(ann, fake_links_service).target
        assert expected == actual


class TestAnnotationJSONPresenter(object):
    def test_asdict(self, document_asdict, fake_links_service):
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
                    'links': {'giraffe': 'http://giraffe.com',
                              'toad': 'http://toad.net'},
                    'references': ['referenced-id-1', 'referenced-id-2'],
                    'extra-1': 'foo',
                    'extra-2': 'bar'}

        result = AnnotationJSONPresenter(ann, fake_links_service).asdict()

        assert result == expected

    def test_asdict_extra_cannot_override_other_data(self, document_asdict, fake_links_service):
        ann = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(ann, fake_links_service).asdict()
        assert presented['id'] == 'the-real-id'

    def test_asdict_extra_uses_copy_of_extra(self, document_asdict, fake_links_service):
        extra = {'foo': 'bar'}
        ann = mock.Mock(id='my-id', extra=extra)
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(ann, fake_links_service).asdict()

        # Presenting the annotation shouldn't change the "extra" dict.
        assert extra == {'foo': 'bar'}

    @pytest.mark.parametrize('annotation,action,expected', [
        (mock.Mock(userid='acct:luke', shared=False), 'read', ['acct:luke']),
        (mock.Mock(groupid='__world__', shared=True), 'read', ['group:__world__']),
        (mock.Mock(groupid='lulapalooza', shared=True), 'read', ['group:lulapalooza']),
        (mock.Mock(userid='acct:luke'), 'admin', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'update', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), 'delete', ['acct:luke']),
        ])
    def test_permissions(self, annotation, action, expected, fake_links_service):
        presenter = AnnotationJSONPresenter(annotation, fake_links_service)
        assert expected == presenter.permissions[action]

    @pytest.fixture
    def document_asdict(self, patch):
        return patch('memex.presenters.DocumentJSONPresenter.asdict')


@pytest.mark.usefixtures('DocumentJSONPresenter')
class TestAnnotationSearchIndexPresenter(object):

    def test_asdict(self, DocumentJSONPresenter):
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

        annotation_dict = AnnotationSearchIndexPresenter(annotation).asdict()

        assert annotation_dict == {
            'id': 'xyz123',
            'created': '2016-02-24T18:03:25.000768+00:00',
            'updated': '2016-02-29T10:24:05.000564+00:00',
            'user': 'acct:luke@hypothes.is',
            'user_raw': 'acct:luke@hypothes.is',
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

    def test_asdict_extra_cannot_override_other_data(self):
        annotation = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})

        annotation_dict = AnnotationSearchIndexPresenter(annotation).asdict()

        assert annotation_dict['id'] == 'the-real-id'

    def test_asdict_does_not_modify_extra(self):
        extra = {'foo': 'bar'}
        annotation = mock.Mock(id='my-id', extra=extra)

        AnnotationSearchIndexPresenter(annotation).asdict()

        assert extra == {'foo': 'bar'}, (
                "Presenting the annotation shouldn't change the 'extra' dict")

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
    def test_permissions(self, annotation, action, expected):
        presenter = AnnotationSearchIndexPresenter(annotation)

        assert expected == presenter.permissions[action]

    def test_it_copies_target_uri_normalized_to_target_scope(self):
        annotation = mock.Mock(
            target_uri_normalized='http://example.com/normalized',
            extra={})

        annotation_dict = AnnotationSearchIndexPresenter(annotation).asdict()

        assert annotation_dict['target'][0]['scope'] == [
            'http://example.com/normalized']

    @pytest.fixture
    def DocumentJSONPresenter(self, patch):
        class_ = patch('memex.presenters.DocumentJSONPresenter')
        class_.return_value.asdict.return_value = {}
        return class_


class TestAnnotationJSONLDPresenter(object):

    def test_asdict(self, fake_links_service):
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
            'id': 'http://fake-link/jsonld_id',
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

        result = AnnotationJSONLDPresenter(annotation, fake_links_service).asdict()

        assert result == expected

    def test_id_returns_jsonld_id_link(self, fake_links_service):
        annotation = mock.Mock(id='foobar')

        presenter = AnnotationJSONLDPresenter(annotation, fake_links_service)

        assert presenter.id == 'http://fake-link/jsonld_id'

    def test_id_passes_annotation_to_link_service(self, fake_links_service):
        annotation = mock.Mock(id='foobar')

        presenter = AnnotationJSONLDPresenter(annotation, fake_links_service)
        _ = presenter.id

        assert fake_links_service.last_annotation == annotation

    def test_bodies_returns_textual_body(self, fake_links_service):
        annotation = mock.Mock(text='Flib flob flab', tags=None)

        bodies = AnnotationJSONLDPresenter(annotation, fake_links_service).bodies

        assert bodies == [{
            'type': 'TextualBody',
            'text': 'Flib flob flab',
            'format': 'text/markdown',
        }]

    def test_bodies_appends_tag_bodies(self, fake_links_service):
        annotation = mock.Mock(text='Flib flob flab', tags=['giraffe', 'lion'])

        bodies = AnnotationJSONLDPresenter(annotation, fake_links_service).bodies

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


class TestDocumentJSONPresenter(object):
    def test_asdict(self, db_session):
        document = models.Document(
            title='Foo',
            document_uris=[models.DocumentURI(uri='http://foo.com', claimant='http://foo.com'),
                           models.DocumentURI(uri='http://foo.org', claimant='http://foo.com', type='rel-canonical')])
        db_session.add(document)
        db_session.flush()

        presenter = DocumentJSONPresenter(document)
        expected = {'title': ['Foo']}
        assert expected == presenter.asdict()

    def test_asdict_when_none_document(self):
        assert {} == DocumentJSONPresenter(None).asdict()

    def test_asdict_does_not_render_other_meta_than_title(self, db_session):
        document = models.Document(
            title='Foo',
            meta=[models.DocumentMeta(type='title', value=['Foo'], claimant='http://foo.com'),
                  models.DocumentMeta(type='twitter.url', value=['http://foo.com'], claimant='http://foo.com'),
                  models.DocumentMeta(type='facebook.title', value=['FB Title'], claimant='http://foo.com')])
        db_session.add(document)
        db_session.flush()

        presenter = DocumentJSONPresenter(document)
        assert {'title': ['Foo']} == presenter.asdict()


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


class FakeLinksService(object):
    def __init__(self):
        self.last_annotation = None

    def get(self, annotation, name):
        self.last_annotation = annotation
        return 'http://fake-link/' + name

    def get_all(self, annotation):
        self.last_annotation = annotation
        return {'giraffe': 'http://giraffe.com', 'toad': 'http://toad.net'}


@pytest.fixture
def fake_links_service():
    return FakeLinksService()

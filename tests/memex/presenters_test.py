# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import mock
import pytest

from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from memex import models
from memex.presenters import AnnotationBasePresenter
from memex.presenters import AnnotationJSONPresenter
from memex.presenters import AnnotationSearchIndexPresenter
from memex.presenters import AnnotationJSONLDPresenter
from memex.presenters import DocumentJSONPresenter
from memex.presenters import DocumentSearchIndexPresenter
from memex.presenters import utc_iso8601, deep_merge_dict
from memex.resources import AnnotationResource


class TestAnnotationBasePresenter(object):

    def test_constructor_args(self):
        annotation = mock.Mock()
        resource = mock.Mock(annotation=annotation)

        presenter = AnnotationBasePresenter(resource)

        assert presenter.annotation_resource == resource
        assert presenter.annotation == annotation

    def test_created_returns_none_if_missing(self):
        annotation = mock.Mock(created=None)
        resource = mock.Mock(annotation=annotation)

        created = AnnotationBasePresenter(resource).created

        assert created is None

    def test_created_uses_iso_format(self):
        when = datetime.datetime(2012, 3, 14, 23, 34, 47, 12)
        annotation = mock.Mock(created=when)
        resource = mock.Mock(annotation=annotation)

        created = AnnotationBasePresenter(resource).created

        assert created == '2012-03-14T23:34:47.000012+00:00'

    def test_updated_returns_none_if_missing(self):
        annotation = mock.Mock(updated=None)
        resource = mock.Mock(annotation=annotation)

        updated = AnnotationBasePresenter(resource).updated

        assert updated is None

    def test_updated_uses_iso_format(self):
        when = datetime.datetime(1983, 8, 31, 7, 18, 20, 98763)
        annotation = mock.Mock(updated=when)
        resource = mock.Mock(annotation=annotation)

        updated = AnnotationBasePresenter(resource).updated

        assert updated == '1983-08-31T07:18:20.098763+00:00'

    def test_links(self):
        annotation = mock.Mock()
        resource = mock.Mock(annotation=annotation)

        links = AnnotationBasePresenter(resource).links
        assert links == resource.links

    def test_text(self):
        annotation = mock.Mock(text='It is magical!')
        resource = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(resource)

        assert 'It is magical!' == presenter.text

    def test_text_missing(self):
        annotation = mock.Mock(text=None)
        resource = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(resource)

        assert '' == presenter.text

    def test_tags(self):
        annotation = mock.Mock(tags=['interesting', 'magic'])
        resource = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(resource)

        assert ['interesting', 'magic'] == presenter.tags

    def test_tags_missing(self):
        annotation = mock.Mock(tags=None)
        resource = mock.Mock(annotation=annotation)
        presenter = AnnotationBasePresenter(resource)

        assert [] == presenter.tags

    def test_target(self):
        annotation = mock.Mock(target_uri='http://example.com',
                               target_selectors={'PositionSelector': {'start': 0, 'end': 12}})
        resource = mock.Mock(annotation=annotation)

        expected = [{'source': 'http://example.com', 'selector': {'PositionSelector': {'start': 0, 'end': 12}}}]
        actual = AnnotationBasePresenter(resource).target
        assert expected == actual

    def test_target_missing_selectors(self):
        annotation = mock.Mock(target_uri='http://example.com',
                               target_selectors=None)
        resource = mock.Mock(annotation=annotation)

        expected = [{'source': 'http://example.com'}]
        actual = AnnotationBasePresenter(resource).target
        assert expected == actual


class TestAnnotationJSONPresenter(object):
    def test_asdict(self, document_asdict, group_service, fake_links_service):
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
        resource = AnnotationResource(ann, group_service, fake_links_service)

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

        result = AnnotationJSONPresenter(resource).asdict()

        assert result == expected

    def test_asdict_extra_cannot_override_other_data(self, document_asdict, group_service, fake_links_service):
        ann = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})
        resource = AnnotationResource(ann, group_service, fake_links_service)
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(resource).asdict()
        assert presented['id'] == 'the-real-id'

    def test_asdict_extra_uses_copy_of_extra(self, document_asdict, group_service, fake_links_service):
        extra = {'foo': 'bar'}
        ann = mock.Mock(id='my-id', extra=extra)
        resource = AnnotationResource(ann, group_service, fake_links_service)
        document_asdict.return_value = {}

        AnnotationJSONPresenter(resource).asdict()

        # Presenting the annotation shouldn't change the "extra" dict.
        assert extra == {'foo': 'bar'}

    @pytest.mark.usefixtures('policy')
    @pytest.mark.parametrize('annotation,group_readable,action,expected', [
        (mock.Mock(userid='acct:luke', shared=False), 'world', 'read', ['acct:luke']),
        (mock.Mock(userid='acct:luke', groupid='abcde', shared=False), 'members', 'read', ['acct:luke']),
        (mock.Mock(groupid='__world__', shared=True), 'world', 'read', ['group:__world__']),
        (mock.Mock(groupid='lulapalooza', shared=True), 'members', 'read', ['group:lulapalooza']),
        (mock.Mock(groupid='publisher', shared=True), 'world', 'read', ['group:__world__']),
        (mock.Mock(userid='acct:luke'), None, 'admin', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), None, 'update', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), None, 'delete', ['acct:luke']),
        ])
    def test_permissions(self, annotation, group_readable, action, expected, group_service, fake_links_service):
        annotation.deleted = False

        group_principals = {
            'members': (security.Allow, 'group:{}'.format(annotation.groupid), 'read'),
            'world': (security.Allow, security.Everyone, 'read'),
            None: security.DENY_ALL,
        }
        group = mock.Mock(spec_set=['__acl__'])
        group.__acl__.return_value = [group_principals[group_readable]]
        group_service.find.return_value = group

        resource = AnnotationResource(annotation, group_service, fake_links_service)
        presenter = AnnotationJSONPresenter(resource)
        assert expected == presenter.permissions[action]

    @pytest.fixture
    def document_asdict(self, patch):
        return patch('memex.presenters.DocumentJSONPresenter.asdict')

    @pytest.fixture
    def policy(self, pyramid_config):
        """Set up a fake authentication policy with a real ACL authorization policy."""
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(None)
        pyramid_config.set_authorization_policy(policy)


@pytest.mark.usefixtures('DocumentSearchIndexPresenter')
class TestAnnotationSearchIndexPresenter(object):

    def test_asdict(self, DocumentSearchIndexPresenter):
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
        DocumentSearchIndexPresenter.return_value.asdict.return_value = {'foo': 'bar'}

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
            'tags_raw': ['magic'],
            'group': '__world__',
            'shared': True,
            'target': [{'scope': ['http://example.com/normalized'],
                        'source': 'http://example.com',
                        'selector': [{'TestSelector': 'foobar'}]}],
            'document': {'foo': 'bar'},
            'references': ['referenced-id-1', 'referenced-id-2'],
        }

    def test_it_copies_target_uri_normalized_to_target_scope(self):
        annotation = mock.Mock(
            target_uri_normalized='http://example.com/normalized',
            extra={})

        annotation_dict = AnnotationSearchIndexPresenter(annotation).asdict()

        assert annotation_dict['target'][0]['scope'] == [
            'http://example.com/normalized']

    @pytest.fixture
    def DocumentSearchIndexPresenter(self, patch):
        class_ = patch('memex.presenters.DocumentSearchIndexPresenter')
        class_.return_value.asdict.return_value = {}
        return class_


class TestAnnotationJSONLDPresenter(object):

    def test_asdict(self, group_service, fake_links_service):
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

        resource = AnnotationResource(annotation, group_service, fake_links_service)
        result = AnnotationJSONLDPresenter(resource).asdict()

        assert result == expected

    def test_id_returns_jsonld_id_link(self, group_service, fake_links_service):
        annotation = mock.Mock(id='foobar')
        resource = AnnotationResource(annotation, group_service, fake_links_service)

        presenter = AnnotationJSONLDPresenter(resource)

        assert presenter.id == 'http://fake-link/jsonld_id'

    def test_id_passes_annotation_to_link_service(self, group_service, fake_links_service):
        annotation = mock.Mock(id='foobar')
        resource = AnnotationResource(annotation, group_service, fake_links_service)

        presenter = AnnotationJSONLDPresenter(resource)
        _ = presenter.id

        assert fake_links_service.last_annotation == annotation

    def test_bodies_returns_textual_body(self, group_service, fake_links_service):
        annotation = mock.Mock(text='Flib flob flab', tags=None)
        resource = AnnotationResource(annotation, group_service, fake_links_service)

        bodies = AnnotationJSONLDPresenter(resource).bodies

        assert bodies == [{
            'type': 'TextualBody',
            'text': 'Flib flob flab',
            'format': 'text/markdown',
        }]

    def test_bodies_appends_tag_bodies(self, group_service, fake_links_service):
        annotation = mock.Mock(text='Flib flob flab', tags=['giraffe', 'lion'])
        resource = AnnotationResource(annotation, group_service, fake_links_service)

        bodies = AnnotationJSONLDPresenter(resource).bodies

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


class TestDocumentSearchIndexPresenter(object):
    @pytest.mark.parametrize('document,expected', [
        (models.Document(title='Foo'), {'title': ['Foo']}),
        (models.Document(title=''), {}),
        (models.Document(title=None), {}),
        (models.Document(web_uri='http://foo.org'), {'web_uri': 'http://foo.org'}),
        (models.Document(web_uri=''), {}),
        (models.Document(web_uri=None), {}),
        (models.Document(title='Foo', web_uri='http://foo.org'), {'title': ['Foo'], 'web_uri': 'http://foo.org'}),
        (None, {})
    ])
    def test_asdict(self, document, expected):
        assert expected == DocumentSearchIndexPresenter(document).asdict()


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


@pytest.fixture
def group_service():
    return mock.Mock(spec_set=['find'])

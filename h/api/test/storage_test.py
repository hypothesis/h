# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy

import pytest
import mock
from pyramid.testing import DummyRequest

from h import db
from h.api import storage
from h.api import schemas
from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentURI


class TestFetchAnnotation(object):

    def test_elastic(self, postgres_enabled, models):
        postgres_enabled.return_value = False
        models.elastic.Annotation.fetch.return_value = mock.Mock()

        actual = storage.fetch_annotation(DummyRequest(), '123')

        models.elastic.Annotation.fetch.assert_called_once_with('123')
        assert models.elastic.Annotation.fetch.return_value == actual

    def test_postgres(self, postgres_enabled):
        request = DummyRequest(db=db.Session)
        postgres_enabled.return_value = True

        annotation = Annotation(userid='luke')
        db.Session.add(annotation)
        db.Session.flush()

        actual = storage.fetch_annotation(request, annotation.id)
        assert annotation == actual

    def test_it_uses_postgres_if_postgres_arg_is_True(self, postgres_enabled):
        """If postgres=True it uses postgres even if feature flag is off."""
        request = DummyRequest(db=db.Session)
        postgres_enabled.return_value = False  # The feature flag is off.
        annotation = Annotation(userid='luke')
        db.Session.add(annotation)
        db.Session.flush()

        actual = storage.fetch_annotation(
            request, annotation.id, _postgres=True)

        assert annotation == actual

    def test_it_uses_elastic_if_postgres_arg_is_False(self,
                                                      postgres_enabled,
                                                      models):
        """If postgres=False it uses elastic even if the feature flag is on."""
        postgres_enabled.return_value = True  # The feature flag is on.
        models.elastic.Annotation.fetch.return_value = mock.Mock()

        actual = storage.fetch_annotation(
            DummyRequest(), '123', _postgres=False)

        models.elastic.Annotation.fetch.assert_called_once_with('123')
        assert models.elastic.Annotation.fetch.return_value == actual

    def test_it_does_not_crash_if_id_is_invalid(self):
        request = DummyRequest(db=db.Session)
        postgres_enabled.return_value = True

        assert storage.fetch_annotation(request, 'foo', _postgres=True) is None


class TestExpandURI(object):

    def test_expand_uri_postgres_no_document(self, postgres_enabled):
        request = DummyRequest(db=db.Session)
        postgres_enabled.return_value = True

        actual = storage.expand_uri(request, 'http://example.com/')
        assert actual == ['http://example.com/']

    def test_expand_uri_elastic_no_document(self, postgres_enabled, models):
        postgres_enabled.return_value = False
        request = DummyRequest()
        models.elastic.Document.get_by_uri.return_value = None
        assert storage.expand_uri(request, "http://example.com/") == [
            "http://example.com/"]

    def test_expand_uri_postgres_document_doesnt_expand_canonical_uris(
            self,
            postgres_enabled):
        request = DummyRequest(db=db.Session)
        postgres_enabled.return_value = True

        document = Document(document_uris=[
            DocumentURI(uri='http://foo.com/', claimant='http://example.com'),
            DocumentURI(uri='http://bar.com/', claimant='http://example.com'),
            DocumentURI(uri='http://example.com/', type='rel-canonical',
                        claimant='http://example.com'),
        ])
        db.Session.add(document)
        db.Session.flush()

        assert storage.expand_uri(request, "http://example.com/") == [
            "http://example.com/"]

    def test_expand_uri_elastic_document_doesnt_expand_canonical_uris(
            self,
            postgres_enabled,
            models):
        postgres_enabled.return_value = False

        request = DummyRequest()
        document = models.elastic.Document.get_by_uri.return_value
        type(document).document_uris = uris = mock.PropertyMock()
        uris.return_value = [
            mock.Mock(uri='http://foo.com/'),
            mock.Mock(uri='http://bar.com/'),
            mock.Mock(uri='http://example.com/', type='rel-canonical'),
        ]
        assert storage.expand_uri(request, "http://example.com/") == [
            "http://example.com/"]

    def test_expand_uri_postgres_document_uris(self, postgres_enabled):
        request = DummyRequest(db=db.Session)
        postgres_enabled.return_value = True

        document = Document(document_uris=[
            DocumentURI(uri='http://foo.com/', claimant='http://bar.com'),
            DocumentURI(uri='http://bar.com/', claimant='http://bar.com'),
        ])
        db.Session.add(document)
        db.Session.flush()

        assert storage.expand_uri(request, 'http://foo.com/') == [
            'http://foo.com/',
            'http://bar.com/'
        ]

    def test_expand_uri_elastic_document_uris(self, postgres_enabled, models):
        postgres_enabled.return_value = False
        request = DummyRequest()
        document = models.elastic.Document.get_by_uri.return_value
        type(document).document_uris = uris = mock.PropertyMock()
        uris.return_value = [
            mock.Mock(uri="http://foo.com/"),
            mock.Mock(uri="http://bar.com/"),
        ]
        assert storage.expand_uri(request, "http://example.com/") == [
            "http://foo.com/",
            "http://bar.com/",
        ]


@pytest.mark.usefixtures('AnnotationTransformEvent',
                         'models',  # Don't try to talk to real Elasticsearch!
                         'partial',
                         'transform')
class TestLegacyCreateAnnotation(object):

    def test_it_inits_an_elastic_annotation_model(self, models):
        data = self.annotation_data()

        storage.legacy_create_annotation(self.mock_request(), data)

        models.elastic.Annotation.assert_called_once_with(data)

    def test_it_calls_partial(self, partial):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        partial.assert_called_once_with(
            storage.fetch_annotation, request, _postgres=False)

    def test_it_calls_prepare(self, models, partial, transform):
        storage.legacy_create_annotation(self.mock_request(),
                                         self.annotation_data())
        transform.prepare.assert_called_once_with(
            models.elastic.Annotation.return_value, partial.return_value)

    def test_it_inits_AnnotationTransformEvent(self,
                                               AnnotationTransformEvent,
                                               models):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        AnnotationTransformEvent.assert_called_once_with(
            request, models.elastic.Annotation.return_value)

    def test_it_calls_notify(self, AnnotationTransformEvent):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        request.registry.notify.assert_called_once_with(
            AnnotationTransformEvent.return_value)

    def test_it_calls_annotation_save(self, models):
        storage.legacy_create_annotation(self.mock_request(),
                                         self.annotation_data())

        models.elastic.Annotation.return_value.save.assert_called_once_with()

    def test_it_returns_the_annotation(self, models):
        result = storage.legacy_create_annotation(self.mock_request(),
                                                  self.annotation_data())

        assert result == models.elastic.Annotation.return_value

    def mock_request(self):
        request = DummyRequest(feature=mock.Mock(spec=lambda feature: False,
                               return_value=False))
        request.registry.notify = mock.Mock(spec=lambda event: None)
        return request

    def annotation_data(self):
        return {'foo': 'bar'}


@pytest.mark.usefixtures('AnnotationTransformEvent',
                         'models',
                         'transform')
class TestLegacyUpdateAnnotation(object):

    def test_it_fetches_the_annotation(self, models):
        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         {})

        models.elastic.Annotation.fetch.assert_called_once_with(
            'test_annotation_id')

    def test_it_calls_update(self, models):
        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         mock.sentinel.data)

        models.elastic.Annotation.fetch.return_value.update\
            .assert_called_once_with(mock.sentinel.data)

    def test_it_calls_partial(self, partial):
        request = DummyRequest()

        storage.legacy_update_annotation(request, 'test_annotation_id', {})

        partial.assert_called_once_with(
            storage.fetch_annotation, request, _postgres=False)

    def test_it_calls_prepare(self, models, partial, transform):
        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         {})

        transform.prepare.assert_called_once_with(
            models.elastic.Annotation.fetch.return_value, partial.return_value)

    def test_it_inits_AnnotationBeforeSaveEvent(self,
                                                AnnotationTransformEvent,
                                                models):
        request = DummyRequest()

        storage.legacy_update_annotation(request, 'test_annotation_id', {})

        AnnotationTransformEvent.assert_called_once_with(
            request, models.elastic.Annotation.fetch.return_value)

    def test_it_calls_notify(self, AnnotationTransformEvent):
        request = DummyRequest()
        request.registry.notify = mock.Mock()

        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         {})

        request.registry.notify.assert_called_once_with(
            AnnotationTransformEvent.return_value)

    def test_it_calls_save(self, models):
        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         {})

        models.elastic.Annotation.fetch.return_value.save\
            .assert_called_once_with()

    def test_it_returns_the_annotation(self, models):
        returned = storage.legacy_update_annotation(DummyRequest(),
                                                    'test_annotation_id',
                                                    {})

        assert returned == models.elastic.Annotation.fetch.return_value


@pytest.mark.usefixtures('models',
                         'update_document_metadata')
class TestCreateAnnotation(object):

    def test_it_fetches_parent_annotation_for_replies(self,
                                                      authn_policy,
                                                      fetch_annotation):
        request = self.mock_request()

        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = 'test-group'

        # The request will need permission to write to 'test-group'.
        authn_policy.effective_principals.return_value = ['group:test-group']

        data = self.annotation_data()

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        storage.create_annotation(request, data)

        fetch_annotation.assert_called_once_with(request,
                                                 'parent_annotation_id',
                                                 _postgres=True)

    def test_it_sets_group_for_replies(self,
                                       authn_policy,
                                       fetch_annotation,
                                       models):
        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = 'test-group'

        # The request will need permission to write to 'test-group'.
        authn_policy.effective_principals.return_value = ['group:test-group']

        data = self.annotation_data()
        assert data['groupid'] != 'test-group'

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        storage.create_annotation(self.mock_request(), data)

        assert models.Annotation.call_args[1]['groupid'] == 'test-group'

    def test_it_raises_if_parent_annotation_does_not_exist(self,
                                                           fetch_annotation):
        fetch_annotation.return_value = None

        data = self.annotation_data()

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        with pytest.raises(schemas.ValidationError) as err:
            storage.create_annotation(self.mock_request(), data)

        assert str(err.value).startswith('references.0: ')

    def test_it_raises_if_user_does_not_have_permissions_for_group(self):
        data = self.annotation_data()
        data['groupid'] = 'foo-group'

        with pytest.raises(schemas.ValidationError) as err:
            storage.create_annotation(self.mock_request(), data)

        assert str(err.value).startswith('group: ')

    def test_it_inits_an_Annotation_model(self, models):
        data = self.annotation_data()

        storage.create_annotation(self.mock_request(), copy.deepcopy(data))

        del data['document']
        models.Annotation.assert_called_once_with(**data)

    def test_it_adds_the_annotation_to_the_database(self, models):
        request = self.mock_request()

        storage.create_annotation(request, self.annotation_data())

        request.db.add.assert_called_once_with(models.Annotation.return_value)

    def test_it_calls_update_document_metadata(self,
                                               models,
                                               update_document_metadata):
        request = self.mock_request()
        annotation_data = self.annotation_data()
        annotation_data['document']['document_meta_dicts'] = (
            mock.sentinel.document_meta_dicts)
        annotation_data['document']['document_uri_dicts'] = (
            mock.sentinel.document_uri_dicts)

        annotation = storage.create_annotation(request, annotation_data)

        update_document_metadata.assert_called_once_with(
            request.db,
            models.Annotation.return_value,
            mock.sentinel.document_meta_dicts,
            mock.sentinel.document_uri_dicts
        )

    def test_it_returns_the_annotation(self, models):
        annotation = storage.create_annotation(self.mock_request(),
                                               self.annotation_data())

        assert annotation == models.Annotation.return_value

    def test_it_does_not_crash_if_target_selectors_is_empty(self):
        # Page notes have [] for target_selectors.
        data = self.annotation_data()
        data['target_selectors'] = []

        storage.create_annotation(self.mock_request(), data)

    def test_it_does_not_crash_if_no_text_or_tags(self):
        # Highlights have no text or tags.
        data = self.annotation_data()
        data['text'] = data['tags'] = ''

        storage.create_annotation(self.mock_request(), data)

    def mock_request(self):
        request = DummyRequest(
            feature=mock.Mock(
                side_effect=lambda flag: flag == "postgres_write"),
            authenticated_userid='acct:test@localhost'
        )

        request.registry.notify = mock.Mock(spec=lambda event: None)

        class DBSpec(object):
            def add(self, annotation):
                pass
            def flush():
                pass
        request.db = mock.Mock(spec=DBSpec)

        return request

    def annotation_data(self):
        return {
            'userid': 'acct:test@localhost',
            'text': 'text',
            'tags': ['one', 'two'],
            'shared': False,
            'target_uri': 'http://www.example.com/example.html',
            'groupid': '__world__',
            'references': [],
            'target_selectors': ['selector_one', 'selector_two'],
            'document': {
                'document_uri_dicts': [],
                'document_meta_dicts': [],
            }
        }


class TestUpdateDocumentMetadata(object):

    def test_it_calls_find_or_create_by_uris(self,
                                             annotation,
                                             models,
                                             session):
        document_uri_dicts = [
            {
                'uri': 'http://example.com/example_1',
                'claimant': 'http://example.com/claimant',
                'type': 'type',
                'content_type': None,
            },
            {
                'uri': 'http://example.com/example_2',
                'claimant': 'http://example.com/claimant',
                'type': 'type',
                'content_type': None,
            },
            {
                'uri': 'http://example.com/example_3',
                'claimant': 'http://example.com/claimant',
                'type': 'type',
                'content_type': None,
            },
        ]

        storage.update_document_metadata(session,
                                         annotation,
                                         [],
                                         document_uri_dicts)

        models.Document.find_or_create_by_uris.assert_called_once_with(
            session,
            annotation.target_uri,
            [
                'http://example.com/example_1',
                'http://example.com/example_2',
                'http://example.com/example_3',
            ],
            created=annotation.created,
            updated=annotation.updated,
        )

    def test_it_calls_merge_documents(self, annotation, session, models):
        """If it finds more than one document it calls merge_documents()."""
        models.Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=3))

        storage.update_document_metadata(session, annotation, [], [])

        models.merge_documents.assert_called_once_with(
            session,
            models.Document.find_or_create_by_uris.return_value,
            updated=annotation.updated)

    def test_it_calls_first(self, annotation, session, models):
        """If it finds only one document it calls first()."""
        models.Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=1))

        storage.update_document_metadata(session, annotation, [], [])

        models.Document.find_or_create_by_uris.return_value\
            .first.assert_called_once_with()

    def test_it_updates_document_updated(self, annotation, session, models):
        yesterday = "yesterday"
        document = models.merge_documents.return_value = mock.Mock(
            updated=yesterday)
        models.Document.find_or_create_by_uris.return_value.first\
            .return_value = document

        storage.update_document_metadata(session, annotation, [], [])

        assert document.updated == annotation.updated

    def test_it_calls_create_or_update_document_uri(self,
                                                    session,
                                                    annotation,
                                                    models):
        models.Document.find_or_create_by_uris.return_value.count\
            .return_value = 1

        document_uri_dicts = [
            {
                'uri': 'http://example.com/example_1',
                'claimant': 'http://example.com/claimant',
                'type': 'type',
                'content_type': None,
            },
            {
                'uri': 'http://example.com/example_2',
                'claimant': 'http://example.com/claimant',
                'type': 'type',
                'content_type': None,
            },
            {
                'uri': 'http://example.com/example_3',
                'claimant': 'http://example.com/claimant',
                'type': 'type',
                'content_type': None,
            },
        ]

        storage.update_document_metadata(session,
                                         annotation,
                                         [],
                                         document_uri_dicts)

        assert models.create_or_update_document_uri.call_count == 3
        for doc_uri_dict in document_uri_dicts:
            models.create_or_update_document_uri.assert_any_call(
                session=session,
                document=models.Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **doc_uri_dict
            )

    def test_it_calls_create_or_update_document_meta(self,
                                                     annotation,
                                                     session,
                                                     models):
        models.Document.find_or_create_by_uris.return_value.count\
            .return_value = 1

        document_meta_dicts = [
            {
                'claimant': 'http://example.com/claimant',
                'claimant_normalized':
                    'http://example.com/claimant_normalized',
                'type': 'title',
                'value': 'foo',
            },
            {
                'type': 'article title',
                'claimant_normalized':
                    'http://example.com/claimant_normalized',
                'value': 'bar',
                'claimant': 'http://example.com/claimant',
            },
            {
                'type': 'site title',
                'claimant_normalized':
                    'http://example.com/claimant_normalized',
                'value': 'gar',
                'claimant': 'http://example.com/claimant',
            },
        ]

        storage.update_document_metadata(session,
                                         annotation,
                                         document_meta_dicts,
                                         [])

        assert models.create_or_update_document_meta.call_count == 3
        for document_meta_dict in document_meta_dicts:
            models.create_or_update_document_meta.assert_any_call(
                session=session,
                document=models.Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **document_meta_dict
            )

    @pytest.fixture
    def annotation(self):
        return mock.Mock(spec=Annotation())

    @pytest.fixture
    def session(self):
        return mock.Mock(spec=db.Session)


@pytest.mark.usefixtures('models',
                         'update_document_metadata')
class TestUpdateAnnotation(object):

    def test_it_calls_get(self, annotation_data, models):
        storage.update_annotation(mock.Mock(),
                                  'test_annotation_id',
                                  annotation_data)

        models.Annotation.query.get.assert_called_once_with(
            'test_annotation_id')

    def test_it_updates_the_annotation(self, annotation_data, models):
        annotation = models.Annotation.query.get.return_value
        storage.update_annotation(mock.Mock(),
                                  'test_annotation_id',
                                  annotation_data)

        for key, value in annotation_data.items():
            assert getattr(annotation, key) == value

    def test_it_adds_new_extras(self, annotation_data, models):
        annotation = models.Annotation.query.get.return_value
        annotation.extra = {}
        annotation_data['extra'] = {'foo': 'bar'}

        storage.update_annotation(mock.Mock(),
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra == {'foo': 'bar'}

    def test_it_overwrites_existing_extras(self, annotation_data, models):
        annotation = models.Annotation.query.get.return_value
        annotation.extra = {'foo': 'original_value'}
        annotation_data['extra'] = {'foo': 'new_value'}

        storage.update_annotation(mock.Mock(),
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra == {'foo': 'new_value'}

    def test_it_does_not_change_extras_that_are_not_sent(self,
                                                         annotation_data,
                                                         models):
        annotation = models.Annotation.query.get.return_value
        annotation.extra = {
            'one': 1,
            'two': 2,
        }
        annotation_data['extra'] = {'two': 22}

        storage.update_annotation(mock.Mock(),
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra['one'] == 1

    def test_it_does_not_change_extras_if_none_are_sent(self,
                                                        annotation_data,
                                                        models):
        annotation = models.Annotation.query.get.return_value
        annotation.extra = {'one': 1, 'two': 2}
        assert 'extra' not in annotation_data

        storage.update_annotation(mock.Mock(),
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra == {'one': 1, 'two': 2}

    def test_it_calls_update_document_metadata(self,
                                               annotation_data,
                                               models,
                                               update_document_metadata):
        annotation = models.Annotation.query.get.return_value
        annotation_data['document']['document_meta_dicts'] = (
            mock.sentinel.document_meta_dicts)
        annotation_data['document']['document_uri_dicts'] = (
            mock.sentinel.document_uri_dicts)

        storage.update_annotation(mock.sentinel.session,
                                  'test_annotation_id',
                                  annotation_data)

        update_document_metadata.assert_called_once_with(
            mock.sentinel.session,
            annotation,
            mock.sentinel.document_meta_dicts,
            mock.sentinel.document_uri_dicts
        )

    def test_it_returns_the_annotation(self, annotation_data, models):
        annotation = storage.update_annotation(mock.Mock(),
                                               'test_annotation_id',
                                               annotation_data)

        assert annotation == models.Annotation.query.get.return_value

    def test_it_does_not_crash_if_no_document_in_data(self):

        storage.update_annotation(mock.Mock(), 'test_annotation_id', {})

    def test_it_does_not_call_update_document_meta_if_no_document_in_data(
            self,
            update_document_metadata):
        storage.update_annotation(mock.Mock(), 'test_annotation_id', {})

        assert not update_document_metadata.called

    @pytest.fixture
    def annotation_data(self):
        return {
            'userid': 'acct:test@localhost',
            'text': 'text',
            'tags': ['one', 'two'],
            'shared': False,
            'target_uri': 'http://www.example.com/example.html',
            'groupid': '__world__',
            'references': [],
            'target_selectors': ['selector_one', 'selector_two'],
            'document': {
                'document_uri_dicts': [],
                'document_meta_dicts': [],
            }
        }


@pytest.mark.usefixtures('fetch_annotation')
class TestDeleteAnnotationLegacy(object):

    """Tests for delete_annotation() when the postgres feature flag is off."""

    def test_it_only_fetches_the_legacy_annotation(self, fetch_annotation):
        request = self.mock_request()

        storage.delete_annotation(request, "test_id")

        fetch_annotation.assert_called_once_with(
            request, "test_id", _postgres=False)

    def test_it_deletes_the_legacy_annotation(self, fetch_annotation):
        storage.delete_annotation(self.mock_request(), "test_id")

        fetch_annotation.return_value.delete.assert_called_once_with()

    def mock_request(self):
        request = DummyRequest()
        request.feature = mock.Mock(return_value=False)
        return request


@pytest.mark.usefixtures('fetch_annotation')
class TestDeleteAnnotation(object):

    def test_it_fetches_the_annotation(self, fetch_annotation):
        request = self.mock_request()

        storage.delete_annotation(request, "test_id")

        assert fetch_annotation.call_args_list[0] == mock.call(request,
                                                               "test_id",
                                                               _postgres=True)

    def test_it_deletes_the_annotation(self, fetch_annotation):
        request = self.mock_request()
        first_return_value = mock.Mock()
        second_return_value = mock.Mock()
        fetch_annotation.side_effect = [
            first_return_value,
            second_return_value,
        ]

        storage.delete_annotation(request, "test_id")

        request.db.delete.assert_called_once_with(first_return_value)

    def test_it_fetches_the_legacy_annotation(self, fetch_annotation):
        request = self.mock_request()

        storage.delete_annotation(request, "test_id")

        assert fetch_annotation.call_args == mock.call(request,
                                                       "test_id",
                                                       _postgres=False)

    def test_it_deletes_the_legacy_annotation(self, fetch_annotation):
        first_return_value = mock.Mock()
        second_return_value = mock.Mock()
        fetch_annotation.side_effect = [
            first_return_value,
            second_return_value,
        ]

        storage.delete_annotation(self.mock_request(), "test_id")

        second_return_value.delete.assert_called_once_with()

    def mock_request(self):
        request = DummyRequest()
        request.feature = mock.Mock(return_value=True)
        request.db = mock.Mock(spec=db.Session)
        return request


@pytest.fixture
def AnnotationTransformEvent(patch):
    return patch('h.api.storage.AnnotationTransformEvent')


@pytest.fixture
def fetch_annotation(patch):
    return patch('h.api.storage.fetch_annotation')


@pytest.fixture
def models(patch):
    models = patch('h.api.storage.models', autospec=False)
    models.Annotation.return_value.is_reply = False
    models.Annotation.query.get.return_value.extra = {}
    return models


@pytest.fixture
def partial(patch):
    return patch('h.api.storage.partial')


@pytest.fixture
def postgres_enabled(patch):
    return patch('h.api.storage._postgres_enabled')


@pytest.fixture
def transform(patch):
    return patch('h.api.storage.transform')


@pytest.fixture
def update_document_metadata(patch):
    return patch('h.api.storage.update_document_metadata')

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


@pytest.mark.usefixtures('AnnotationBeforeSaveEvent',
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

    def test_it_inits_AnnotationBeforeSaveEvent(self,
                                                AnnotationBeforeSaveEvent,
                                                models):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        AnnotationBeforeSaveEvent.assert_called_once_with(
            request, models.elastic.Annotation.return_value)

    def test_it_calls_notify(self, AnnotationBeforeSaveEvent):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        request.registry.notify.assert_called_once_with(
            AnnotationBeforeSaveEvent.return_value)

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

    @pytest.fixture
    def AnnotationBeforeSaveEvent(self, patch):
        return patch('h.api.storage.AnnotationBeforeSaveEvent')

    @pytest.fixture
    def partial(self, patch):
        return patch('h.api.storage.partial')

    @pytest.fixture
    def transform(self, patch):
        return patch('h.api.storage.transform')


@pytest.mark.usefixtures('fetch_annotation',
                         'models')
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

    def test_it_calls_find_or_create_by_uris(self, models):
        request = self.mock_request()
        annotation = models.Annotation.return_value
        annotation_data = self.annotation_data()
        annotation_data['document']['document_uri_dicts'] = [
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

        storage.create_annotation(request, annotation_data)

        models.Document.find_or_create_by_uris.assert_called_once_with(
            request.db,
            annotation.target_uri,
            [
                'http://example.com/example_1',
                'http://example.com/example_2',
                'http://example.com/example_3',
            ],
            created=annotation.created,
            updated=annotation.updated,
        )

    def test_it_calls_merge_documents(self, models):
        """If it finds more than one document it calls merge_documents()."""
        models.Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=3))
        request = self.mock_request()

        storage.create_annotation(request, self.annotation_data())

        models.merge_documents.assert_called_once_with(
            request.db,
            models.Document.find_or_create_by_uris.return_value,
            updated=models.Annotation.return_value.updated,
        )

    def test_it_calls_first(self, models):
        """If it finds only one document it calls first()."""
        models.Document.find_or_create_by_uris.return_value = mock.Mock(
            count=mock.Mock(return_value=1))

        storage.create_annotation(self.mock_request(), self.annotation_data())

        models.Document.find_or_create_by_uris.return_value\
            .first.assert_called_once_with()

    def test_it_updates_document_updated(self, models):
        yesterday = "yesterday"
        document = models.merge_documents.return_value = mock.Mock(
            updated=yesterday)
        models.Document.find_or_create_by_uris.return_value.first\
            .return_value = document

        storage.create_annotation(self.mock_request(), self.annotation_data())

        assert document.updated == models.Annotation.return_value.updated

    def test_it_calls_create_or_update_document_uri(
            self,
            models):
        models.Document.find_or_create_by_uris.return_value.count\
            .return_value = 1

        request = self.mock_request()

        annotation = models.Annotation.return_value

        annotation_data = self.annotation_data()
        annotation_data['document']['document_uri_dicts'] = [
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

        storage.create_annotation(request, copy.deepcopy(annotation_data))

        assert models.create_or_update_document_uri.call_count == 3
        for doc_uri_dict in annotation_data['document']['document_uri_dicts']:
            models.create_or_update_document_uri.assert_any_call(
                session=request.db,
                document=models.Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **doc_uri_dict
            )

    def test_it_calls_create_or_update_document_meta(self, models):
        models.Document.find_or_create_by_uris.return_value.count\
            .return_value = 1

        request = self.mock_request()

        annotation = models.Annotation.return_value

        annotation_data = self.annotation_data()
        annotation_data['document']['document_meta_dicts'] = [
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

        storage.create_annotation(request, copy.deepcopy(annotation_data))

        assert models.create_or_update_document_meta.call_count == 3
        for document_meta_dict in annotation_data['document'][
                'document_meta_dicts']:
            models.create_or_update_document_meta.assert_any_call(
                session=request.db,
                document=models.Document.find_or_create_by_uris.return_value.first.return_value,
                created=annotation.created,
                updated=annotation.updated,
                **document_meta_dict
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
def fetch_annotation(patch):
    return patch('h.api.storage.fetch_annotation')


@pytest.fixture
def models(patch):
    models = patch('h.api.storage.models', autospec=False)
    models.Annotation.return_value.is_reply = False
    return models


@pytest.fixture
def postgres_enabled(patch):
    return patch('h.api.storage._postgres_enabled')

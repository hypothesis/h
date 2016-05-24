# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy

import pytest
import mock
from pyramid.testing import DummyRequest

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

    def test_postgres(self, db_session, postgres_enabled):
        request = DummyRequest(db=db_session)
        postgres_enabled.return_value = True

        annotation = Annotation(userid='luke')
        db_session.add(annotation)
        db_session.flush()

        actual = storage.fetch_annotation(request, annotation.id)
        assert annotation == actual

    def test_it_uses_postgres_if_postgres_arg_is_True(self, db_session, postgres_enabled):
        """If postgres=True it uses postgres even if feature flag is off."""
        request = DummyRequest(db=db_session)
        postgres_enabled.return_value = False  # The feature flag is off.
        annotation = Annotation(userid='luke')
        db_session.add(annotation)
        db_session.flush()

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

    def test_it_does_not_crash_if_id_is_invalid(self, db_session):
        request = DummyRequest(db=db_session)
        postgres_enabled.return_value = True

        assert storage.fetch_annotation(request, 'foo', _postgres=True) is None


class TestExpandURI(object):

    def test_expand_uri_no_document(self, db_session):
        request = DummyRequest(db=db_session)

        actual = storage.expand_uri(request, 'http://example.com/')
        assert actual == ['http://example.com/']

    def test_expand_uri_document_doesnt_expand_canonical_uris(self, db_session):
        request = DummyRequest(db=db_session)

        document = Document(document_uris=[
            DocumentURI(uri='http://foo.com/', claimant='http://example.com'),
            DocumentURI(uri='http://bar.com/', claimant='http://example.com'),
            DocumentURI(uri='http://example.com/', type='rel-canonical',
                        claimant='http://example.com'),
        ])
        db_session.add(document)
        db_session.flush()

        assert storage.expand_uri(request, "http://example.com/") == [
            "http://example.com/"]

    def test_expand_uri_document_uris(self, db_session):
        request = DummyRequest(db=db_session)

        document = Document(document_uris=[
            DocumentURI(uri='http://foo.com/', claimant='http://bar.com'),
            DocumentURI(uri='http://bar.com/', claimant='http://bar.com'),
        ])
        db_session.add(document)
        db_session.flush()

        assert storage.expand_uri(request, 'http://foo.com/') == [
            'http://foo.com/',
            'http://bar.com/'
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

    def test_it_creates_a_fetcher_function(self, partial):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        partial.assert_called_once_with(
            storage.fetch_annotation, request, _postgres=False)

    def test_it_prepares_the_annotation_for_indexing(self,
                                                     models,
                                                     partial,
                                                     transform):
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

    def test_it_fires_the_AnnotationTransformEvent(self,
                                                   AnnotationTransformEvent):
        request = self.mock_request()

        storage.legacy_create_annotation(request, self.annotation_data())

        request.registry.notify.assert_called_once_with(
            AnnotationTransformEvent.return_value)

    def test_it_saves_the_annotation_to_Elasticsearch(self, models):
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

    def test_it_updates_the_annotation_object(self, models):
        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         mock.sentinel.data)

        models.elastic.Annotation.fetch.return_value.update\
            .assert_called_once_with(mock.sentinel.data)

    def test_it_creates_a_fetcher_function(self, partial):
        request = DummyRequest()

        storage.legacy_update_annotation(request, 'test_annotation_id', {})

        partial.assert_called_once_with(
            storage.fetch_annotation, request, _postgres=False)

    def test_it_prepares_the_annotation_for_indexing(self,
                                                     models,
                                                     partial,
                                                     transform):
        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         {})

        transform.prepare.assert_called_once_with(
            models.elastic.Annotation.fetch.return_value, partial.return_value)

    def test_it_inits_AnnotationTransformEvent(self,
                                               AnnotationTransformEvent,
                                               models):
        request = DummyRequest()

        storage.legacy_update_annotation(request, 'test_annotation_id', {})

        AnnotationTransformEvent.assert_called_once_with(
            request, models.elastic.Annotation.fetch.return_value)

    def test_it_fires_the_AnnotationTransformEvent(self,
                                                   AnnotationTransformEvent):
        request = DummyRequest()
        request.registry.notify = mock.Mock()

        storage.legacy_update_annotation(DummyRequest(),
                                         'test_annotation_id',
                                         {})

        request.registry.notify.assert_called_once_with(
            AnnotationTransformEvent.return_value)

    def test_it_saves_the_annotation_to_Elasticsearch(self, models):
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
                                                      config,
                                                      fetch_annotation):
        request = self.mock_request()

        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = 'test-group'

        # The request will need permission to write to 'test-group'.
        config.testing_securitypolicy('acct:foo@example.com', groupids=['group:test-group'])

        data = self.annotation_data()

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        storage.create_annotation(request, data)

        fetch_annotation.assert_called_once_with(request,
                                                 'parent_annotation_id',
                                                 _postgres=True)

    def test_it_sets_group_for_replies(self,
                                       config,
                                       fetch_annotation,
                                       models):
        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = 'test-group'

        # The request will need permission to write to 'test-group'.
        config.testing_securitypolicy('acct:foo@example.com', groupids=['group:test-group'])

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

        with pytest.raises(schemas.ValidationError) as exc:
            storage.create_annotation(self.mock_request(), data)

        assert str(exc.value).startswith('references.0: ')

    def test_it_raises_if_user_does_not_have_permissions_for_group(self):
        data = self.annotation_data()
        data['groupid'] = 'foo-group'

        with pytest.raises(schemas.ValidationError) as exc:
            storage.create_annotation(self.mock_request(), data)

        assert str(exc.value).startswith('group: ')

    def test_it_inits_an_Annotation_model(self, models):
        data = self.annotation_data()

        storage.create_annotation(self.mock_request(), copy.deepcopy(data))

        del data['document']
        models.Annotation.assert_called_once_with(**data)

    def test_it_adds_the_annotation_to_the_database(self, models):
        request = self.mock_request()

        storage.create_annotation(request, self.annotation_data())

        request.db.add.assert_called_once_with(models.Annotation.return_value)

    def test_it_updates_the_document_metadata_from_the_annotation(
            self,
            models,
            update_document_metadata):
        request = self.mock_request()
        annotation_data = self.annotation_data()
        annotation_data['document']['document_meta_dicts'] = (
            mock.sentinel.document_meta_dicts)
        annotation_data['document']['document_uri_dicts'] = (
            mock.sentinel.document_uri_dicts)

        storage.create_annotation(request, annotation_data)

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


@pytest.mark.usefixtures('models',
                         'update_document_metadata')
class TestUpdateAnnotation(object):

    def test_it_gets_the_annotation_model(self,
                                          annotation_data,
                                          models,
                                          session):
        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        session.query.assert_called_once_with(models.Annotation)
        session.query.return_value.get.assert_called_once_with(
            'test_annotation_id')

    def test_it_adds_new_extras(self, annotation_data, session):
        annotation = session.query.return_value.get.return_value
        annotation.extra = {}
        annotation_data['extra'] = {'foo': 'bar'}

        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra == {'foo': 'bar'}

    def test_it_overwrites_existing_extras(self,
                                           annotation_data,
                                           session):
        annotation = session.query.return_value.get.return_value
        annotation.extra = {'foo': 'original_value'}
        annotation_data['extra'] = {'foo': 'new_value'}

        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra == {'foo': 'new_value'}

    def test_it_does_not_change_extras_that_are_not_sent(self,
                                                         annotation_data,
                                                         session):
        annotation = session.query.return_value.get.return_value
        annotation.extra = {
            'one': 1,
            'two': 2,
        }
        annotation_data['extra'] = {'two': 22}

        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra['one'] == 1

    def test_it_does_not_change_extras_if_none_are_sent(self,
                                                        annotation_data,
                                                        session):
        annotation = session.query.return_value.get.return_value
        annotation.extra = {'one': 1, 'two': 2}
        assert not annotation_data.get('extra')

        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        assert annotation.extra == {'one': 1, 'two': 2}

    def test_it_updates_the_annotation(self, annotation_data, session):
        annotation = session.query.return_value.get.return_value

        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        for key, value in annotation_data.items():
            assert getattr(annotation, key) == value

    def test_it_updates_the_document_metadata_from_the_annotation(
            self,
            annotation_data,
            session,
            update_document_metadata):
        annotation = session.query.return_value.get.return_value
        annotation_data['document']['document_meta_dicts'] = (
            mock.sentinel.document_meta_dicts)
        annotation_data['document']['document_uri_dicts'] = (
            mock.sentinel.document_uri_dicts)

        storage.update_annotation(session,
                                  'test_annotation_id',
                                  annotation_data)

        update_document_metadata.assert_called_once_with(
            session,
            annotation,
            mock.sentinel.document_meta_dicts,
            mock.sentinel.document_uri_dicts
        )

    def test_it_returns_the_annotation(self, annotation_data, session):
        annotation = storage.update_annotation(session,
                                               'test_annotation_id',
                                               annotation_data)

        assert annotation == session.query.return_value.get.return_value

    def test_it_does_not_crash_if_no_document_in_data(self,
                                                      session):
        storage.update_annotation(session, 'test_annotation_id', {})

    def test_it_does_not_call_update_document_meta_if_no_document_in_data(
            self,
            session,
            update_document_metadata):

        storage.update_annotation(session, 'test_annotation_id', {})

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
            },
            'extra': {},
        }


@pytest.mark.usefixtures('fetch_annotation')
class TestDeleteAnnotation(object):

    def test_it_fetches_the_annotation(self, fetch_annotation, mock_request):
        storage.delete_annotation(mock_request, "test_id")

        assert fetch_annotation.call_args_list[0] == mock.call(mock_request,
                                                               "test_id",
                                                               _postgres=True)

    def test_it_deletes_the_annotation(self, fetch_annotation, mock_request):
        first_return_value = mock.Mock()
        second_return_value = mock.Mock()
        fetch_annotation.side_effect = [
            first_return_value,
            second_return_value,
        ]

        storage.delete_annotation(mock_request, "test_id")

        mock_request.db.delete.assert_called_once_with(first_return_value)

    @pytest.fixture
    def mock_request(self, session):
        request = DummyRequest()
        request.feature = mock.Mock(return_value=True)
        request.db = session
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
    return models


@pytest.fixture
def partial(patch):
    return patch('h.api.storage.partial')


@pytest.fixture
def postgres_enabled(patch):
    return patch('h.api.storage._postgres_enabled')


@pytest.fixture
def session(db_session):
    session = mock.Mock(spec=db_session)
    session.query.return_value.get.return_value.extra = {}
    return session


@pytest.fixture
def transform(patch):
    return patch('h.api.storage.transform')


@pytest.fixture
def update_document_metadata(patch):
    return patch('h.api.storage.models.update_document_metadata')

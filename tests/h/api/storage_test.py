# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy

import pytest
import mock

from h.api import storage
from h.api import schemas
from h.api.models.annotation import Annotation
from h.api.models.document import Document, DocumentURI, DocumentMeta


class TestFetchAnnotation(object):

    def test_it_fetches_and_returns_the_annotation(self, db_session):
        annotation = Annotation(userid='luke')
        db_session.add(annotation)
        db_session.flush()

        actual = storage.fetch_annotation(db_session, annotation.id)
        assert annotation == actual

    def test_it_does_not_crash_if_id_is_invalid(self, db_session):
        assert storage.fetch_annotation(db_session, 'foo') is None


class TestFetchOrderedAnnotations(object):

    def test_it_returns_annotations_for_ids_in_the_same_order(self, db_session):
        ann_1 = Annotation(userid='luke')
        ann_2 = Annotation(userid='luke')
        db_session.add_all([ann_1, ann_2])
        db_session.flush()

        assert [ann_2, ann_1] == storage.fetch_ordered_annotations(db_session,
                                                                   [ann_2.id, ann_1.id])
        assert [ann_1, ann_2] == storage.fetch_ordered_annotations(db_session,
                                                                   [ann_1.id, ann_2.id])

    def test_it_allows_to_change_the_query(self, db_session):
        ann_1 = Annotation(userid='luke', target_uri='http://example.com')
        ann_2 = Annotation(userid='maria', target_uri='http://example.com')
        db_session.add_all([ann_1, ann_2])

        doc = Document(
            document_uris=[DocumentURI(uri='http://bar.com/', claimant='http://example.com'),
                           DocumentURI(uri='http://example.com/', type='rel-canonical', claimant='http://example.com')],
            meta=[DocumentMeta(claimant='http://example.com', type='title', value='Example')])
        db_session.add(doc)

        db_session.flush()

        def only_maria(query):
            return query.filter(Annotation.userid == 'maria')

        assert [ann_2] == storage.fetch_ordered_annotations(db_session,
                                                            [ann_2.id, ann_1.id],
                                                            query_processor=only_maria)


class TestExpandURI(object):

    def test_expand_uri_no_document(self, db_session):
        actual = storage.expand_uri(db_session, 'http://example.com/')
        assert actual == ['http://example.com/']

    def test_expand_uri_document_doesnt_expand_canonical_uris(self, db_session):
        document = Document(document_uris=[
            DocumentURI(uri='http://foo.com/', claimant='http://example.com'),
            DocumentURI(uri='http://bar.com/', claimant='http://example.com'),
            DocumentURI(uri='http://example.com/', type='rel-canonical',
                        claimant='http://example.com'),
        ])
        db_session.add(document)
        db_session.flush()

        assert storage.expand_uri(db_session, "http://example.com/") == [
            "http://example.com/"]

    def test_expand_uri_document_uris(self, db_session):
        document = Document(document_uris=[
            DocumentURI(uri='http://foo.com/', claimant='http://bar.com'),
            DocumentURI(uri='http://bar.com/', claimant='http://bar.com'),
        ])
        db_session.add(document)
        db_session.flush()

        assert storage.expand_uri(db_session, 'http://foo.com/') == [
            'http://foo.com/',
            'http://bar.com/'
        ]


@pytest.mark.usefixtures('models',
                         'update_document_metadata')
class TestCreateAnnotation(object):

    def test_it_fetches_parent_annotation_for_replies(self,
                                                      config,
                                                      fetch_annotation,
                                                      pyramid_request):

        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = 'test-group'

        # The request will need permission to write to 'test-group'.
        config.testing_securitypolicy('acct:foo@example.com', groupids=['group:test-group'])

        data = self.annotation_data()

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        storage.create_annotation(pyramid_request, data)

        fetch_annotation.assert_called_once_with(pyramid_request.db,
                                                 'parent_annotation_id')

    def test_it_sets_group_for_replies(self,
                                       config,
                                       fetch_annotation,
                                       models,
                                       pyramid_request):
        # Make the annotation's parent belong to 'test-group'.
        fetch_annotation.return_value.groupid = 'test-group'

        # The request will need permission to write to 'test-group'.
        config.testing_securitypolicy('acct:foo@example.com', groupids=['group:test-group'])

        data = self.annotation_data()
        assert data['groupid'] != 'test-group'

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        storage.create_annotation(pyramid_request, data)

        assert models.Annotation.call_args[1]['groupid'] == 'test-group'

    def test_it_raises_if_parent_annotation_does_not_exist(self,
                                                           fetch_annotation,
                                                           pyramid_request):
        fetch_annotation.return_value = None

        data = self.annotation_data()

        # The annotation is a reply.
        data['references'] = ['parent_annotation_id']

        with pytest.raises(schemas.ValidationError) as exc:
            storage.create_annotation(pyramid_request, data)

        assert str(exc.value).startswith('references.0: ')

    def test_it_raises_if_user_does_not_have_permissions_for_group(self, pyramid_request):
        data = self.annotation_data()
        data['groupid'] = 'foo-group'

        with pytest.raises(schemas.ValidationError) as exc:
            storage.create_annotation(pyramid_request, data)

        assert str(exc.value).startswith('group: ')

    def test_it_inits_an_Annotation_model(self, models, pyramid_request):
        data = self.annotation_data()

        storage.create_annotation(pyramid_request, copy.deepcopy(data))

        del data['document']
        models.Annotation.assert_called_once_with(**data)

    def test_it_adds_the_annotation_to_the_database(self, models, pyramid_request):
        storage.create_annotation(pyramid_request, self.annotation_data())

        assert models.Annotation.return_value in pyramid_request.db.added

    def test_it_updates_the_document_metadata_from_the_annotation(self,
                                                                  models,
                                                                  pyramid_request,
                                                                  update_document_metadata):
        annotation_data = self.annotation_data()
        annotation_data['document']['document_meta_dicts'] = (
            mock.sentinel.document_meta_dicts)
        annotation_data['document']['document_uri_dicts'] = (
            mock.sentinel.document_uri_dicts)

        storage.create_annotation(pyramid_request, annotation_data)

        update_document_metadata.assert_called_once_with(
            pyramid_request.db,
            models.Annotation.return_value,
            mock.sentinel.document_meta_dicts,
            mock.sentinel.document_uri_dicts
        )

    def test_it_returns_the_annotation(self, models, pyramid_request):
        annotation = storage.create_annotation(pyramid_request,
                                               self.annotation_data())

        assert annotation == models.Annotation.return_value

    def test_it_does_not_crash_if_target_selectors_is_empty(self, pyramid_request):
        # Page notes have [] for target_selectors.
        data = self.annotation_data()
        data['target_selectors'] = []

        storage.create_annotation(pyramid_request, data)

    def test_it_does_not_crash_if_no_text_or_tags(self, pyramid_request):
        # Highlights have no text or tags.
        data = self.annotation_data()
        data['text'] = data['tags'] = ''

        storage.create_annotation(pyramid_request, data)

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


class TestDeleteAnnotation(object):

    def test_it_deletes_the_annotation(self, db_session):
        ann_1 = Annotation(userid='luke')
        ann_2 = Annotation(userid='leia')
        db_session.add_all([ann_1, ann_2])
        db_session.flush()

        storage.delete_annotation(db_session, ann_1.id)
        db_session.commit()

        assert db_session.query(Annotation).get(ann_1.id) is None
        assert db_session.query(Annotation).get(ann_2.id) == ann_2


@pytest.fixture
def fetch_annotation(patch):
    return patch('h.api.storage.fetch_annotation')


@pytest.fixture
def models(patch):
    models = patch('h.api.storage.models', autospec=False)
    models.Annotation.return_value.is_reply = False
    return models


@pytest.fixture
def pyramid_request(fake_db_session, pyramid_request):
    pyramid_request.db = fake_db_session
    return pyramid_request


@pytest.fixture
def session(db_session):
    session = mock.Mock(spec=db_session)
    session.query.return_value.get.return_value.extra = {}
    return session


@pytest.fixture
def update_document_metadata(patch):
    return patch('h.api.storage.models.update_document_metadata')

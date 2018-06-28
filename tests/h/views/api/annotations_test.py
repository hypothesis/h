# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import mock
import pytest

from pyramid import testing
from pyramid.config import Configurator

from h.schemas import ValidationError
from h.search.core import SearchResult
from h.views.api import annotations as views
from h.exceptions import PayloadError


class TestIndex(object):

    def test_it_returns_the_right_links(self, pyramid_config, pyramid_request):

        # Scan `h.views.api_annotations` for API link metadata specified in @api_config
        # declarations.
        config = Configurator()
        config.scan('h.views.api.annotations')
        pyramid_request.registry.api_links = config.registry.api_links

        pyramid_config.add_route('api.search', '/dummy/search')
        pyramid_config.add_route('api.annotations', '/dummy/annotations')
        pyramid_config.add_route('api.annotation', '/dummy/annotations/:id')
        pyramid_config.add_route('api.links', '/dummy/links')

        result = views.index(testing.DummyResource(), pyramid_request)

        host = 'http://example.com'  # Pyramid's default host URL'
        links = result['links']
        assert links['annotation']['create']['method'] == 'POST'
        assert links['annotation']['create']['url'] == (
            host + '/dummy/annotations')
        assert links['annotation']['delete']['method'] == 'DELETE'
        assert links['annotation']['delete']['url'] == (
            host + '/dummy/annotations/:id')
        assert links['annotation']['read']['method'] == 'GET'
        assert links['annotation']['read']['url'] == (
            host + '/dummy/annotations/:id')
        assert links['annotation']['update']['method'] == 'PATCH'
        assert links['annotation']['update']['url'] == (
            host + '/dummy/annotations/:id')
        assert links['search']['method'] == 'GET'
        assert links['search']['url'] == host + '/dummy/search'


class TestLinks(object):

    def test_it_returns_the_right_links(self, pyramid_config, pyramid_request):
        pyramid_config.add_route('account', '/account/settings')
        pyramid_config.add_route('forgot_password', '/forgot-password')
        pyramid_config.add_route('group_create', '/groups/new')
        pyramid_config.add_route('help', '/docs/help')
        pyramid_config.add_route('oauth_authorize', '/oauth/authorize')
        pyramid_config.add_route('oauth_revoke', '/oauth/revoke')
        pyramid_config.add_route('activity.search', '/search')
        pyramid_config.add_route('signup', '/signup')
        pyramid_config.add_route('stream.user_query', '/u/{user}')

        links = views.links(testing.DummyResource(), pyramid_request)

        host = 'http://example.com'  # Pyramid's default host URL.
        assert links == {
            'account.settings': host + '/account/settings',
            'forgot-password': host + '/forgot-password',
            'groups.new': host + '/groups/new',
            'help': host + '/docs/help',
            'oauth.authorize': host + '/oauth/authorize',
            'oauth.revoke': host + '/oauth/revoke',
            'search.tag': host + '/search?q=tag:":tag"',
            'signup': host + '/signup',
            'user': host + '/u/:user',
        }


@pytest.mark.usefixtures('presentation_service', 'search_lib')
class TestSearch(object):

    def test_it_searches(self, pyramid_request, search_lib):
        pyramid_request.stats = mock.Mock()

        views.search(pyramid_request)

        search = search_lib.Search.return_value
        search_lib.Search.assert_called_with(pyramid_request,
                                             separate_replies=False,
                                             stats=pyramid_request.stats)
        search.run.assert_called_once_with(pyramid_request.params)

    def test_it_presents_search_results(self, pyramid_request, search_run, presentation_service):
        search_run.return_value = SearchResult(2, ['row-1', 'row-2'], [], {})

        views.search(pyramid_request)

        presentation_service.present_all.assert_called_once_with(['row-1', 'row-2'])

    def test_it_returns_search_results(self, pyramid_request, search_run, presentation_service):
        search_run.return_value = SearchResult(2, ['row-1', 'row-2'], [], {})

        expected = {
            'total': 2,
            'rows': presentation_service.present_all.return_value
        }

        assert views.search(pyramid_request) == expected

    def test_it_presents_replies(self, pyramid_request, search_run, presentation_service):
        pyramid_request.params = {'_separate_replies': '1'}
        search_run.return_value = SearchResult(1, ['row-1'], ['reply-1', 'reply-2'], {})

        views.search(pyramid_request)

        presentation_service.present_all.assert_called_with(['reply-1', 'reply-2'])

    def test_it_returns_replies(self, pyramid_request, search_run, presentation_service):
        pyramid_request.params = {'_separate_replies': '1'}
        search_run.return_value = SearchResult(1, ['row-1'], ['reply-1', 'reply-2'], {})

        expected = {
            'total': 1,
            'rows': presentation_service.present_all(['row-1']),
            'replies': presentation_service.present_all(['reply-1', 'reply-2'])
        }

        assert views.search(pyramid_request) == expected

    @pytest.fixture
    def search_lib(self, patch):
        return patch('h.views.api.annotations.search_lib')

    @pytest.fixture
    def search_run(self, search_lib):
        return search_lib.Search.return_value.run

    @pytest.fixture
    def storage(self, patch):
        return patch('h.views.api.annotations.storage')


@pytest.mark.usefixtures('AnnotationEvent',
                         'create_schema',
                         'links_service',
                         'group_service',
                         'presentation_service',
                         'storage')
class TestCreate(object):

    def test_it_raises_if_json_parsing_fails(self, pyramid_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(pyramid_request).json_body = {}
        with mock.patch.object(type(pyramid_request),
                               'json_body',
                               new_callable=mock.PropertyMock) as json_body:
            json_body.side_effect = ValueError()
            with pytest.raises(PayloadError):
                views.create(pyramid_request)

    def test_it_inits_CreateAnnotationSchema(self, pyramid_request, create_schema):
        views.create(pyramid_request)

        create_schema.assert_called_once_with(pyramid_request)

    def test_it_validates_the_posted_data(self, pyramid_request, create_schema):
        """It should call validate() with a request.json_body."""
        views.create(pyramid_request)

        create_schema.return_value.validate.assert_called_once_with(pyramid_request.json_body)

    def test_it_raises_if_validate_raises(self, pyramid_request, create_schema):
        create_schema.return_value.validate.side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError) as exc:
            views.create(pyramid_request)

        assert str(exc.value) == 'asplode'

    def test_it_creates_the_annotation_in_storage(self,
                                                  pyramid_request,
                                                  storage,
                                                  create_schema,
                                                  group_service):
        schema = create_schema.return_value

        views.create(pyramid_request)

        storage.create_annotation.assert_called_once_with(
            pyramid_request, schema.validate.return_value, group_service)

    def test_it_raises_if_create_annotation_raises(self,
                                                   pyramid_request,
                                                   storage):
        storage.create_annotation.side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError) as exc:
            views.create(pyramid_request)

        assert str(exc.value) == 'asplode'

    def test_it_publishes_annotation_event(self,
                                           AnnotationEvent,
                                           pyramid_request,
                                           storage):
        """It publishes an annotation "create" event for the annotation."""
        views.create(pyramid_request)

        annotation = storage.create_annotation.return_value

        AnnotationEvent.assert_called_once_with(pyramid_request,
                                                annotation.id,
                                                'create')
        pyramid_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value)

    def test_it_initialises_annotation_resource(self,
                                                storage,
                                                annotation_resource,
                                                pyramid_request,
                                                group_service,
                                                links_service):

        annotation = storage.create_annotation.return_value

        views.create(pyramid_request)

        annotation_resource.assert_called_once_with(
                annotation, group_service, links_service)

    def test_it_presents_annotation(self,
                                    annotation_resource,
                                    presentation_service,
                                    pyramid_request):
        views.create(pyramid_request)

        presentation_service.present.assert_called_once_with(
                annotation_resource.return_value)

    def test_it_returns_presented_annotation(self, presentation_service, pyramid_request):
        result = views.create(pyramid_request)

        assert result == presentation_service.present.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = {}
        pyramid_request.notify_after_commit = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def create_schema(self, patch):
        return patch('h.views.api.annotations.CreateAnnotationSchema')


@pytest.mark.usefixtures('presentation_service')
class TestRead(object):

    def test_it_returns_presented_annotation(self,
                                             presentation_service,
                                             pyramid_request):
        context = mock.Mock()

        result = views.read(context, pyramid_request)

        presentation_service.present.assert_called_once_with(context)

        assert result == presentation_service.present.return_value


@pytest.mark.usefixtures('AnnotationJSONLDPresenter', 'links_service')
class TestReadJSONLD(object):

    def test_it_sets_correct_content_type(self, AnnotationJSONLDPresenter, pyramid_request):
        AnnotationJSONLDPresenter.CONTEXT_URL = 'http://foo.com/context.jsonld'

        context = mock.Mock()

        views.read_jsonld(context, pyramid_request)

        assert pyramid_request.response.content_type == 'application/ld+json'
        assert pyramid_request.response.content_type_params == {
            'charset': 'UTF-8',
            'profile': 'http://foo.com/context.jsonld'
        }

    def test_it_returns_presented_annotation(self,
                                             AnnotationJSONLDPresenter,
                                             pyramid_request):
        context = mock.Mock()
        presenter = mock.Mock()
        AnnotationJSONLDPresenter.return_value = presenter
        AnnotationJSONLDPresenter.CONTEXT_URL = 'http://foo.com/context.jsonld'

        result = views.read_jsonld(context, pyramid_request)

        AnnotationJSONLDPresenter.assert_called_once_with(context)
        assert result == presenter.asdict()

    @pytest.fixture
    def AnnotationJSONLDPresenter(self, patch):
        return patch('h.views.api.annotations.AnnotationJSONLDPresenter')


@pytest.mark.usefixtures('AnnotationEvent',
                         'links_service',
                         'group_service',
                         'presentation_service',
                         'update_schema',
                         'storage')
class TestUpdate(object):

    def test_it_inits_the_schema(self, pyramid_request, update_schema):
        context = mock.Mock()

        views.update(context, pyramid_request)

        update_schema.assert_called_once_with(pyramid_request,
                                              context.annotation.target_uri,
                                              context.annotation.groupid)

    def test_it_raises_if_json_parsing_fails(self, pyramid_request):
        """It raises PayloadError if parsing of the request body fails."""
        # Make accessing the request.json_body property raise ValueError.
        type(pyramid_request).json_body = {}
        with mock.patch.object(type(pyramid_request),
                               'json_body',
                               new_callable=mock.PropertyMock) as json_body:
            json_body.side_effect = ValueError()
            with pytest.raises(PayloadError):
                views.update(mock.Mock(), pyramid_request)

    def test_it_validates_the_posted_data(self, pyramid_request, update_schema):
        context = mock.Mock()
        schema = update_schema.return_value

        views.update(context, pyramid_request)

        schema.validate.assert_called_once_with(pyramid_request.json_body)

    def test_it_raises_if_validate_raises(self, pyramid_request, update_schema):
        update_schema.return_value.validate.side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError):
            views.update(mock.Mock(), pyramid_request)

    def test_it_updates_the_annotation_in_storage(self,
                                                  pyramid_request,
                                                  storage,
                                                  update_schema,
                                                  group_service):
        context = mock.Mock()
        schema = update_schema.return_value
        schema.validate.return_value = mock.sentinel.validated_data

        views.update(context, pyramid_request)

        storage.update_annotation.assert_called_once_with(
            pyramid_request,
            context.annotation.id,
            mock.sentinel.validated_data,
            group_service
        )

    def test_it_raises_if_storage_raises(self, pyramid_request, storage):
        storage.update_annotation.side_effect = ValidationError('asplode')

        with pytest.raises(ValidationError):
            views.update(mock.Mock(), pyramid_request)

    def test_it_inits_an_AnnotationEvent(self,
                                         AnnotationEvent,
                                         storage,
                                         pyramid_request):
        context = mock.Mock()

        views.update(context, pyramid_request)

        AnnotationEvent.assert_called_once_with(pyramid_request,
                                                storage.update_annotation.return_value.id,
                                                'update')

    def test_it_fires_the_AnnotationEvent(self, AnnotationEvent, pyramid_request):
        views.update(mock.Mock(), pyramid_request)

        pyramid_request.notify_after_commit.assert_called_once_with(
            AnnotationEvent.return_value)

    def test_it_initialises_annotation_resource(self,
                                                storage,
                                                annotation_resource,
                                                pyramid_request,
                                                group_service,
                                                links_service):

        annotation = storage.update_annotation.return_value

        views.update(mock.Mock(), pyramid_request)

        annotation_resource.assert_called_once_with(
                annotation, group_service, links_service)

    def test_it_presents_annotation(self,
                                    annotation_resource,
                                    presentation_service,
                                    pyramid_request):
        views.update(mock.Mock(), pyramid_request)

        presentation_service.present.assert_called_once_with(
                annotation_resource.return_value)

    def test_it_returns_a_presented_dict(self,
                                         presentation_service,
                                         pyramid_request):
        returned = views.update(mock.Mock(), pyramid_request)

        assert returned == presentation_service.present.return_value

    def test_it_tracks_deprecated_put_requests(self, pyramid_request):
        pyramid_request.method = 'PUT'
        pyramid_request.stats = mock.Mock(spec_set=['incr'])

        views.update(mock.Mock(), pyramid_request)

        pyramid_request.stats.incr.assert_called_once_with('api.deprecated.put_update_annotation')

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.json_body = {}
        pyramid_request.notify_after_commit = mock.Mock()
        return pyramid_request

    @pytest.fixture
    def update_schema(self, patch):
        return patch('h.views.api.annotations.UpdateAnnotationSchema')


@pytest.mark.usefixtures('AnnotationEvent',
                         'links_service',
                         'storage')
class TestDelete(object):

    def test_it_deletes_then_annotation_from_storage(self, pyramid_request, storage):
        context = mock.Mock()

        views.delete(context, pyramid_request)

        storage.delete_annotation.assert_called_once_with(pyramid_request.db,
                                                          context.annotation.id)

    def test_it_inits_and_fires_an_AnnotationEvent(self,
                                                   AnnotationEvent,
                                                   pyramid_request):
        context = mock.Mock()
        event = AnnotationEvent.return_value

        views.delete(context, pyramid_request)

        AnnotationEvent.assert_called_once_with(pyramid_request,
                                                context.annotation.id,
                                                'delete')
        pyramid_request.notify_after_commit.assert_called_once_with(event)

    def test_it_returns_object(self, pyramid_request):
        context = mock.Mock()

        result = views.delete(context, pyramid_request)

        assert result == {'id': context.annotation.id, 'deleted': True}


@pytest.fixture
def AnnotationEvent(patch):
    return patch('h.views.api.annotations.AnnotationEvent')


@pytest.fixture
def annotation_resource(patch):
    return patch('h.views.api.annotations.AnnotationContext')


@pytest.fixture
def links_service(pyramid_config):
    service = mock.Mock(spec_set=['get', 'get_all'])
    pyramid_config.register_service(service, name='links')
    return service


@pytest.fixture
def presentation_service(pyramid_config):
    svc = mock.Mock(spec_set=['present', 'present_all'])
    pyramid_config.register_service(svc, name='annotation_json_presentation')
    return svc


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.Mock(spec_set=['find'])
    pyramid_config.register_service(group_service, iface='h.interfaces.IGroupService')
    return group_service


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.notify_after_commit = mock.Mock(spec_set=[])
    return pyramid_request


@pytest.fixture
def search_lib(patch):
    return patch('h.views.api.annotations.search_lib')


@pytest.fixture
def storage(patch):
    return patch('h.views.api.annotations.storage')

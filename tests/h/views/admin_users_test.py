# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from mock import Mock
from mock import MagicMock
from mock import call
from pyramid import httpexceptions
import pytest

from h.services.annotation_stats import AnnotationStatsService
from h.services.user import UserService
from h.models import Annotation
from h.views.admin_users import (
    UserDeletionError,
    UserNotFoundError,
    delete_user,
    users_activate,
    users_delete,
    users_index,
)

users_index_fixtures = pytest.mark.usefixtures('models', 'annotation_stats_service')


@users_index_fixtures
def test_users_index(pyramid_request):
    result = users_index(pyramid_request)

    assert result == {
        'default_authority': pyramid_request.authority,
        'username': None,
        'authority': None,
        'user': None,
        'user_meta': {},
    }


@users_index_fixtures
def test_users_index_looks_up_users_by_username(models, pyramid_request):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    users_index(pyramid_request)

    models.User.get_by_username.assert_called_with(
        pyramid_request.db, "bob", "foo.org")


@users_index_fixtures
def test_users_index_looks_up_users_by_email(models, pyramid_request):
    pyramid_request.params = {"username": "bob@builder.com", "authority": "foo.org"}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    users_index(pyramid_request)

    models.User.get_by_email.assert_called_with(pyramid_request.db, "bob@builder.com", "foo.org")


@users_index_fixtures
def test_users_index_strips_spaces(models, pyramid_request):
    pyramid_request.params = {"username": "    bob   ", "authority": "   foo.org    "}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    users_index(pyramid_request)

    models.User.get_by_username.assert_called_with(pyramid_request.db, "bob", "foo.org")


@users_index_fixtures
def test_users_index_queries_annotation_count_by_userid(models, factories, pyramid_request, annotation_stats_service):
    user = factories.User.build(username='bob')
    models.User.get_by_username.return_value = user
    annotation_stats_service.user_annotation_counts.return_value = {'total': 8}

    pyramid_request.params = {"username": "bob", "authority": user.authority}
    result = users_index(pyramid_request)
    assert result['user_meta']['annotations_count'] == 8


@users_index_fixtures
def test_users_index_no_user_found(models, pyramid_request):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    models.User.get_by_username.return_value = None
    models.User.get_by_email.return_value = None

    result = users_index(pyramid_request)

    assert result == {
        'default_authority': "example.com",
        'username': "bob",
        'authority': "foo.org",
        'user': None,
        'user_meta': {}
    }


@users_index_fixtures
def test_users_index_user_found(models, pyramid_request, db_session, factories):
    pyramid_request.params = {"username": "bob", "authority": "foo.org"}
    user = factories.User.build(username='bob', authority='foo.org')
    models.User.get_by_username.return_value = user

    result = users_index(pyramid_request)

    assert result == {
        'default_authority': "example.com",
        'username': "bob",
        'authority': "foo.org",
        'user': user,
        'user_meta': {'annotations_count': 0},
    }


users_activate_fixtures = pytest.mark.usefixtures('user_service', 'ActivationEvent')


@users_activate_fixtures
def test_users_activate_gets_user(user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.org"}

    users_activate(pyramid_request)

    user_service.fetch.assert_called_once_with("acct:bob@example.org")


@users_activate_fixtures
def test_users_activate_user_not_found_error(user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@foo.org"}
    user_service.fetch.return_value = None

    with pytest.raises(UserNotFoundError):
        users_activate(pyramid_request)


@users_activate_fixtures
def test_users_activate_activates_user(user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.org"}

    users_activate(pyramid_request)

    user_service.fetch.return_value.activate.assert_called_once_with()


@users_activate_fixtures
def test_users_activate_flashes_success(pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}

    users_activate(pyramid_request)
    success_flash = pyramid_request.session.peek_flash('success')

    assert success_flash


@users_activate_fixtures
def test_users_activate_inits_ActivationEvent(ActivationEvent, user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}

    users_activate(pyramid_request)

    ActivationEvent.assert_called_once_with(pyramid_request,
                                            user_service.fetch.return_value)


@users_activate_fixtures
def test_users_activate_calls_notify(ActivationEvent, notify, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}

    users_activate(pyramid_request)

    notify.assert_called_once_with(ActivationEvent.return_value)


@users_activate_fixtures
def test_users_activate_redirects(pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}

    result = users_activate(pyramid_request)

    assert isinstance(result, httpexceptions.HTTPFound)


users_delete_fixtures = pytest.mark.usefixtures('user_service', 'fake_delete_user')


@users_delete_fixtures
def test_users_delete_user_not_found_error(user_service, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@foo.org"}

    user_service.fetch.return_value = None

    with pytest.raises(UserNotFoundError):
        users_delete(pyramid_request)


@users_delete_fixtures
def test_users_delete_deletes_user(user_service, fake_delete_user, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}
    user = MagicMock()

    user_service.fetch.return_value = user

    users_delete(pyramid_request)

    fake_delete_user.assert_called_once_with(pyramid_request, user)


@users_delete_fixtures
def test_users_delete_group_creator_error(user_service, fake_delete_user, pyramid_request):
    pyramid_request.params = {"userid": "acct:bob@example.com"}
    user = MagicMock()

    user_service.fetch.return_value = user
    fake_delete_user.side_effect = UserDeletionError('group creator error')

    users_delete(pyramid_request)

    assert pyramid_request.session.peek_flash('error') == [
        'group creator error'
    ]

delete_user_fixtures = pytest.mark.usefixtures('api_storage',
                                               'elasticsearch_helpers',
                                               'models',
                                               'user_created_no_groups')


@delete_user_fixtures
def test_delete_user_raises_when_group_creator(models, pyramid_request):
    user = Mock()

    models.Group.created_by.return_value.count.return_value = 10

    with pytest.raises(UserDeletionError):
        delete_user(pyramid_request, user)


@delete_user_fixtures
def test_delete_user_disassociate_group_memberships(fake_db_session, pyramid_request):
    pyramid_request.db = fake_db_session
    user = Mock(groups=[Mock()])

    delete_user(pyramid_request, user)

    assert user.groups == []


@delete_user_fixtures
def test_delete_user_queries_annotations(elasticsearch_helpers, factories, fake_db_session, pyramid_request):
    pyramid_request.db = fake_db_session
    user = factories.User(username=u'bob')

    delete_user(pyramid_request, user)

    elasticsearch_helpers.scan.assert_called_once_with(
        client=pyramid_request.es.conn,
        query={
            'query': {
                'filtered': {
                    'filter': {'term': {'user': u'acct:bob@example.com'}},
                    'query': {'match_all': {}}
                }
            }
        }
    )


@delete_user_fixtures
def test_delete_user_deletes_annotations(api_storage, elasticsearch_helpers, fake_db_session, pyramid_request):
    pyramid_request.db = fake_db_session
    user = MagicMock()
    annotation_1 = {'_id': 'annotation-1'}
    annotation_2 = {'_id': 'annotation-2'}

    elasticsearch_helpers.scan.return_value = [annotation_1, annotation_2]

    delete_user(pyramid_request, user)

    assert api_storage.delete_annotation.mock_calls == [
        call(pyramid_request.db, 'annotation-1'),
        call(pyramid_request.db, 'annotation-2')
    ]


@delete_user_fixtures
def test_delete_user_deletes_user(fake_db_session, pyramid_request):
    pyramid_request.db = fake_db_session
    user = MagicMock()

    delete_user(pyramid_request, user)

    assert user in pyramid_request.db.deleted


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.es = mock.MagicMock()
    return pyramid_request


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route('admin_users', '/adm/users')


@pytest.fixture
def ActivationEvent(patch):
    return patch('h.views.admin_users.ActivationEvent')


@pytest.fixture
def api_storage(patch):
    return patch('h.views.admin_users.storage')


@pytest.fixture
def fake_delete_user(patch):
    return patch('h.views.admin_users.delete_user')


@pytest.fixture
def elasticsearch_helpers(patch):
    return patch('h.views.admin_users.es_helpers')


@pytest.fixture
def models(patch):
    module = patch('h.views.admin_users.models')
    module.Annotation = Annotation
    return module


@pytest.fixture
def user_service(pyramid_config, db_session):
    service = Mock(spec_set=UserService(default_authority='example.com',
                                        session=db_session))
    pyramid_config.register_service(service, name='user')
    return service


@pytest.fixture
def annotation_stats_service(pyramid_config, db_session):
    service = Mock(spec_set=AnnotationStatsService(session=db_session))
    service.user_annotation_counts.return_value = {'total': 0}
    pyramid_config.register_service(service, name='annotation_stats')
    return service


@pytest.fixture
def user_created_no_groups(models):
    # By default, pretend that all users are the creators of 0 groups.
    models.Group.created_by.return_value.count.return_value = 0

# -*- coding: utf-8 -*-

from mock import Mock
from mock import MagicMock
from mock import call
from pyramid import httpexceptions
from pyramid.testing import DummyRequest as _DummyRequest
import pytest

from h.admin.views import users as views


class DummyRequest(_DummyRequest):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auth_domain', 'example.com')
        super(DummyRequest, self).__init__(*args, **kwargs)


users_index_fixtures = pytest.mark.usefixtures('User')


@users_index_fixtures
def test_users_index():
    request = DummyRequest()

    result = views.users_index(request)

    assert result == {'username': None, 'user': None, 'user_meta': {}}


@users_index_fixtures
def test_users_index_looks_up_users_by_username(User):
    es = MagicMock()
    request = DummyRequest(params={"username": "bob"},
                           es=es)

    views.users_index(request)

    User.get_by_username.assert_called_with("bob")


@users_index_fixtures
def test_users_index_looks_up_users_by_email(User):
    es = MagicMock()
    request = DummyRequest(params={"username": "bob@builder.com"},
                           es=es)

    User.get_by_username.return_value = None

    views.users_index(request)

    User.get_by_email.assert_called_with("bob@builder.com")


@users_index_fixtures
def test_users_index_queries_annotation_count_by_userid(User):
    es = MagicMock()
    request = DummyRequest(params={"username": "Bob"},
                           es=es)

    User.get_by_username.return_value.username = 'Robert'

    views.users_index(request)

    expected_query = {
        'query': {
            'filtered': {
                'filter': {'term': {'user': u'acct:robert@example.com'}},
                'query': {'match_all': {}}
            }
        }
    }
    es.conn.count.assert_called_with(index=es.index,
                                     doc_type=es.t.annotation,
                                     body=expected_query)


@users_index_fixtures
def test_users_index_no_user_found(User):
    es = MagicMock()
    request = DummyRequest(params={"username": "bob"},
                           es=es)
    User.get_by_username.return_value = None
    User.get_by_email.return_value = None

    result = views.users_index(request)

    assert result == {'username': "bob", 'user': None, 'user_meta': {}}


@users_index_fixtures
def test_users_index_user_found(User):
    es = MagicMock()
    request = DummyRequest(params={"username": "bob"},
                           es=es)
    es.conn.count.return_value = {'count': 43}

    result = views.users_index(request)

    assert result == {
        'username': "bob",
        'user': User.get_by_username.return_value,
        'user_meta': {'annotations_count': 43},
    }


users_activate_fixtures = pytest.mark.usefixtures('User', 'ActivationEvent')


@users_activate_fixtures
def test_users_activate_gets_user(User):
    request = DummyRequest(params={"username": "bob"})

    views.users_activate(request)

    User.get_by_username.assert_called_once_with("bob")


@users_activate_fixtures
def test_users_activate_flashes_error_if_no_user(User):
    request = DummyRequest(params={"username": "bob"})
    request.session.flash = Mock()
    User.get_by_username.return_value = None

    views.users_activate(request)

    assert request.session.flash.call_count == 1
    assert request.session.flash.call_args[0][1] == 'error'


@users_activate_fixtures
def test_users_activate_redirects_if_no_user(User):
    request = DummyRequest(params={"username": "bob"})
    User.get_by_username.return_value = None

    result = views.users_activate(request)

    assert isinstance(result, httpexceptions.HTTPFound)


@users_activate_fixtures
def test_users_activate_activates_user(User):
    request = DummyRequest(params={"username": "bob"})

    views.users_activate(request)

    User.get_by_username.return_value.activate.assert_called_once_with()


@users_activate_fixtures
def test_users_activate_flashes_success():
    request = DummyRequest(params={"username": "bob"})
    request.session.flash = Mock()

    views.users_activate(request)

    assert request.session.flash.call_count == 1
    assert request.session.flash.call_args[0][1] == 'success'


@users_activate_fixtures
def test_users_activate_inits_ActivationEvent(ActivationEvent, User):
    request = DummyRequest(params={"username": "bob"})

    views.users_activate(request)

    ActivationEvent.assert_called_once_with(
        request, User.get_by_username.return_value)


@users_activate_fixtures
def test_users_activate_calls_notify(ActivationEvent, User):
    request = DummyRequest(params={"username": "bob"})
    request.registry.notify = Mock(spec=lambda event: None)

    views.users_activate(request)

    request.registry.notify.assert_called_once_with(
        ActivationEvent.return_value)


@users_activate_fixtures
def test_users_activate_redirects(User):
    request = DummyRequest(params={"username": "bob"})

    result = views.users_activate(request)

    assert isinstance(result, httpexceptions.HTTPFound)


users_delete_fixtures = pytest.mark.usefixtures('User', 'delete_user')


@users_delete_fixtures
def test_users_delete_redirect(User):
    request = DummyRequest(params={"username": "bob"})
    User.get_by_username.return_value = None

    result = views.users_delete(request)
    assert result.__class__ == httpexceptions.HTTPFound


@users_delete_fixtures
def test_users_delete_user_not_found_error(User):
    request = DummyRequest(params={"username": "bob"})

    User.get_by_username.return_value = None

    views.users_delete(request)

    assert request.session.peek_flash('error') == [
        'Cannot find user with username bob'
    ]


@users_delete_fixtures
def test_users_delete_deletes_user(User, delete_user):
    request = DummyRequest(params={"username": "bob"})
    user = MagicMock()

    User.get_by_username.return_value = user

    views.users_delete(request)

    delete_user.assert_called_once_with(request, user)


@users_delete_fixtures
def test_users_delete_group_creator_error(User, delete_user):
    request = DummyRequest(params={"username": "bob"})
    user = MagicMock()

    User.get_by_username.return_value = user
    delete_user.side_effect = views.UserDeletionError('group creator error')

    views.users_delete(request)

    assert request.session.peek_flash('error') == [
        'group creator error'
    ]

delete_user_fixtures = pytest.mark.usefixtures('api_storage',
                                               'elasticsearch_helpers',
                                               'models',
                                               'user_created_no_groups')


@delete_user_fixtures
def test_delete_user_raises_when_group_creator(models):
    request, user = Mock(), Mock()

    models.Group.created_by.return_value.count.return_value = 10

    with pytest.raises(views.UserDeletionError):
        views.delete_user(request, user)


@delete_user_fixtures
def test_delete_user_disassociate_group_memberships():
    request = Mock()
    user = Mock(groups=[Mock()])

    views.delete_user(request, user)

    assert user.groups == []


@delete_user_fixtures
def test_delete_user_queries_annotations(elasticsearch_helpers):
    request = DummyRequest(es=Mock(), db=Mock())
    user = MagicMock(username=u'bob')

    views.delete_user(request, user)

    elasticsearch_helpers.scan.assert_called_once_with(
        client=request.es.conn,
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
def test_delete_user_deletes_annotations(elasticsearch_helpers, api_storage):
    request, user = Mock(), MagicMock()
    annotation_1 = {'_id': 'annotation-1'}
    annotation_2 = {'_id': 'annotation-2'}

    elasticsearch_helpers.scan.return_value = [annotation_1, annotation_2]

    views.delete_user(request, user)

    assert api_storage.delete_annotation.mock_calls == [
        call(request, 'annotation-1'),
        call(request, 'annotation-2')
    ]


@delete_user_fixtures
def test_delete_user_deletes_user():
    request, user = Mock(), MagicMock()

    views.delete_user(request, user)

    request.db.delete.assert_called_once_with(user)


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_users', '/adm/users')


@pytest.fixture
def ActivationEvent(patch):
    return patch('h.admin.views.users.ActivationEvent')


@pytest.fixture
def User(patch):
    return patch('h.models.User')


@pytest.fixture
def api_storage(patch):
    return patch('h.admin.views.users.storage')


@pytest.fixture
def delete_user(patch):
    return patch('h.admin.views.users.delete_user')


@pytest.fixture
def elasticsearch_helpers(patch):
    return patch('h.admin.views.users.es_helpers')


@pytest.fixture
def models(patch):
    return patch('h.admin.views.users.models')


@pytest.fixture
def user_created_no_groups(models):
    # By default, pretend that all users are the creators of 0 groups.
    models.Group.created_by.return_value.count.return_value = 0

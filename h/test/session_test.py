# -*- coding: utf-8 -*-
import mock
import pytest

from h import session


# The fixtures required to mock all of model()'s dependencies.
model_fixtures = pytest.mark.usefixtures('groups', 'models')


def _mock_group():
    """Return a mock h.api.groups.models.Group object."""
    group = mock.Mock()
    group.as_dict.return_value = {
        'name': group.name,
        'id': group.hashid.return_value,
    }
    return group


@model_fixtures
def test_model_returns_no_groups_if_no_user():
    request = mock.Mock(authenticated_userid=None)

    assert session.model(request)['groups'] == [
        {'name': 'Public', 'id': '__world__', 'public': True},
    ]


@model_fixtures
def test_model_returns_no_groups_if_user_not_found(models):
    request = mock.Mock(authenticated_userid='unknown-user-id')
    models.User.get_by_userid.return_value = None

    assert session.model(request)['groups'] == [
        {'name': 'Public', 'id': '__world__', 'public': True},
    ]


@model_fixtures
def test_model_returns_no_groups_if_user_has_no_groups(models):
    request = mock.Mock()
    models.User.get_by_userid.return_value.groups = []

    assert session.model(request)['groups'] == [
        {'name': 'Public', 'id': '__world__', 'public': True},
    ]


@model_fixtures
def test_model_calls_as_dict_for_each_of_the_users_groups(models, groups):
    group_1 = _mock_group()
    group_2 = _mock_group()
    group_3 = _mock_group()
    request = mock.Mock()
    models.User.get_by_userid.return_value.groups = [
        group_1, group_2, group_3]

    session.model(request)['groups']

    assert groups.as_dict.call_args_list == [
        mock.call(request, group_1),
        mock.call(request, group_2),
        mock.call(request, group_3)
    ]


@model_fixtures
def test_model_returns_the_group_dicts_from_as_dict(models, groups):
    # In production these would be Group objects not strings.
    models.User.get_by_userid.return_value.groups = [
        'group_1', 'group_2', 'group_3']
    # In production these would be group dicts not strings.
    groups.as_dict.side_effect = ['dict_1', 'dict_2', 'dict_3']

    model = session.model(mock.Mock())

    assert model['groups'] == [
        {'name': 'Public', 'id': '__world__', 'public': True},
        'dict_1', 'dict_2', 'dict_3'
    ]


@pytest.fixture
def groups(request):
    patcher = mock.patch('h.session.groups', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def models(request):
    patcher = mock.patch('h.session.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()

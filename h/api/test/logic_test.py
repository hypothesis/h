# -*- coding: utf-8 -*-
import pytest
import mock

from h.api import logic


def _mock_annotation(**kwargs):
    """Return a mock h.api.models.Annotation object."""
    annotation = mock.MagicMock()
    annotation.__getitem__.side_effect = kwargs.__getitem__
    annotation.__setitem__.side_effect = kwargs.__setitem__
    annotation.get.side_effect = kwargs.get
    annotation.__contains__.side_effect = kwargs.__contains__
    annotation.update.side_effect = kwargs.update
    annotation.pop.side_effect = kwargs.pop
    return annotation


search_annotations_fixtures = pytest.mark.usefixtures('search_lib')


@search_annotations_fixtures
def test_search_calls_search(search_lib):
    """It should call search_lib.search() once."""
    logic.search_annotations(mock.Mock(), [], mock.Mock())

    assert search_lib.search.call_count == 1


@search_annotations_fixtures
def test_search_passes_params_to_search(search_lib):
    """It should pass request.params to search_lib.search()."""
    params = mock.Mock()

    logic.search_annotations(params, [], mock.Mock())

    assert search_lib.search.call_args[0][0] == params


@search_annotations_fixtures
def test_search_passes_effective_principals_to_search(search_lib):
    """It should pass request.effective_principals to search_lib.search()."""
    principals = mock.Mock()

    logic.search_annotations(mock.Mock(), principals, mock.Mock())

    assert search_lib.search.call_args[0][1] == principals


@search_annotations_fixtures
def test_search_passes_user_to_search(search_lib):
    """It should pass the user from get_user() to search_lib.search()."""
    logic.search_annotations(mock.Mock(), [], mock.sentinel.user)

    assert search_lib.search.call_args[1]['user'] == mock.sentinel.user


@search_annotations_fixtures
def test_search_passes_search_normalized_uris(search_lib):
    """It should pass search_normalized from request.feature() to search()."""
    logic.search_annotations(
        mock.Mock(), [], mock.Mock(), mock.sentinel.search_normalized_uris)

    assert search_lib.search.call_args[1]['search_normalized_uris'] == (
        mock.sentinel.search_normalized_uris)


@search_annotations_fixtures
def test_search_returns_total(search_lib):
    """It should return the total from search_lib.search()."""
    search_lib.search.return_value = {
        'total': 3,
        # In production these would be annotation dicts, not strings.
        'rows': ['annotation_1', 'annotation_2', 'annotation_3']
    }

    response_data = logic.search_annotations(mock.Mock(), mock.Mock())

    assert response_data['total'] == 3


@search_annotations_fixtures
def test_search_returns_rendered_annotations(search_lib):
    """It should return the rendered annotations.

    It should pass the annotations from search_lib.search() through
    search_lib.render() and return the results.

    """
    search_lib.search.return_value = {
        'total': 3,
        # In production these would be annotation dicts, not strings.
        'rows': ['annotation_1', 'annotation_2', 'annotation_3']
    }
    # Our mock render function just appends '_rendered' onto our mock
    # annotation strings.
    search_lib.render.side_effect = lambda annotation: annotation + '_rendered'

    response_data = logic.search_annotations(mock.Mock(), mock.Mock())

    assert response_data['rows'] == [
        'annotation_1_rendered', 'annotation_2_rendered',
        'annotation_3_rendered']


# The fixtures required to mock all of create_annotation()'s dependencies.
create_annotation_fixtures = pytest.mark.usefixtures(
    'Annotation', 'search_lib')


@create_annotation_fixtures
def test_create_annotation_pops_protected_fields(Annotation):
    """It should remove any protected fields before calling Annotation."""
    logic.create_annotation(
        fields={
            'foo': 'bar',
            'created': 'foo',
            'updated': 'foo',
            'user': 'foo',
            'consumer': 'foo',
            'id': 'foo'
        },
        user=mock.Mock())

    for field in ('created', 'updated', 'user', 'consumer', 'id'):
        assert field not in Annotation.call_args[0][0]


@create_annotation_fixtures
def test_create_annotation_calls_Annotation(Annotation):
    fields = mock.MagicMock()
    logic.create_annotation(fields, mock.Mock())

    Annotation.assert_called_once_with(fields)


@create_annotation_fixtures
def test_create_annotation_sets_user(Annotation):
    """It should set the annotation's 'user' field to the user's id."""
    user = mock.Mock()
    Annotation.return_value = _mock_annotation()

    annotation = logic.create_annotation({}, user)

    assert annotation['user'] == user.id


@create_annotation_fixtures
def test_create_annotation_sets_consumer(Annotation):
    """It should set the annotation's 'consumer' field to the consumer key."""
    user = mock.Mock()
    Annotation.return_value = _mock_annotation()

    annotation = logic.create_annotation({}, user)

    assert annotation['consumer'] == user.consumer.key


@create_annotation_fixtures
def test_create_annotation_calls_prepare(Annotation, search_lib):
    """It should call prepare() once with the annotation."""
    logic.create_annotation({}, mock.Mock())

    search_lib.prepare.assert_called_once_with(Annotation.return_value)


@create_annotation_fixtures
def test_create_annotation_calls_save(Annotation):
    """It should call save() once."""
    logic.create_annotation({}, mock.Mock())

    Annotation.return_value.save.assert_called_once_with()


@create_annotation_fixtures
def test_create_annotation_returns_the_annotation(Annotation):
    assert logic.create_annotation({}, mock.Mock()) == Annotation.return_value


@create_annotation_fixtures
def test_create_annotation_does_not_crash_if_annotation_has_no_group(
        Annotation):
    assert 'group' not in Annotation.return_value
    fields = {}  # No group here either.

    logic.create_annotation(fields, mock.Mock())


@create_annotation_fixtures
def test_create_annotation_does_not_crash_if_annotations_parent_has_no_group(
        Annotation):
    """It shouldn't crash if the parent annotation has no group.

    It shouldn't crash if the annotation is a reply and its parent annotation
    has no 'group' field.

    """
    # No group in the original annotation/reply itself.
    Annotation.return_value = _mock_annotation()
    assert 'group' not in Annotation.return_value
    fields = {}  # No group here either.

    # And no group in the parent annotation either.
    Annotation.fetch.return_value = {}

    logic.create_annotation(fields, mock.Mock())


# The fixtures required to mock all of update_annotation()'s dependencies.
update_annotation_fixtures = pytest.mark.usefixtures('search_lib')


@update_annotation_fixtures
def test_update_annotation_does_not_pass_protected_fields_to_update():
    annotation = _mock_annotation()

    logic.update_annotation(
        annotation,
        fields={
            'foo': 'bar',
            'created': 'foo',
            'updated': 'foo',
            'user': 'foo',
            'consumer': 'foo',
            'id': 'foo'
        },
        has_admin_permission=False)

    for field in ('created', 'updated', 'user', 'consumer', 'id'):
        assert field not in annotation.update.call_args[0][0]


@update_annotation_fixtures
def test_update_annotation_raises_if_non_admin_changes_perms():
    with pytest.raises(RuntimeError):
        logic.update_annotation(
            _mock_annotation(),
            fields={'permissions': 'changed'},
            has_admin_permission=False)


@update_annotation_fixtures
def test_update_annotation_admins_can_change_permissions():
    annotation = _mock_annotation(permissions='foo')

    logic.update_annotation(
        annotation,
        fields={'permissions': 'changed'},
        has_admin_permission=True)

    assert annotation['permissions'] == 'changed'


@update_annotation_fixtures
def test_update_annotation_non_admins_can_make_non_permissions_changes():
    annotation = _mock_annotation(foo='bar')

    logic.update_annotation(
        annotation,
        fields={'foo': 'changed'},
        has_admin_permission=False)

    assert annotation['foo'] == 'changed'


@update_annotation_fixtures
def test_update_annotation_calls_update():
    annotation = _mock_annotation()
    fields = {'foo': 'bar'}

    logic.update_annotation(annotation, fields, False)

    annotation.update.assert_called_once_with(fields)


@update_annotation_fixtures
def test_update_annotation_user_can_change_group():
    annotation = _mock_annotation(group='old')
    fields = {'group': 'new'}

    logic.update_annotation(annotation, fields, False)

    assert annotation['group'] == 'new'


@update_annotation_fixtures
def test_update_annotation_removes_userid_from_permissions_if_deleted():
    user = 'acct:fred@hypothes.is'
    annotation = _mock_annotation(
        deleted=True,
        user=user,
        permissions={
            'admin': [user, 'someone else'],
            'read': [user, 'someone else'],
            'update': ['someone else'],
            'delete': ['someone else']
        }
    )
    fields = {
        'permissions': {
            'update': [user],
            'delete': [user]
        }
    }

    logic.update_annotation(annotation, fields, True)

    for action in annotation['permissions']:
        assert user not in annotation['permissions'][action]


@update_annotation_fixtures
def test_update_annotation_does_not_remove_userid_if_not_deleted():
    user = 'acct:fred@hypothes.is'
    annotation = _mock_annotation(
        deleted=False,
        user=user,
        permissions={
            'admin': [user, 'someone else'],
            'read': [user, 'someone else'],
            'update': ['someone else'],
            'delete': ['someone else']
        }
    )
    fields = {
        'permissions': {
            'update': [user],
            'delete': [user]
        }
    }

    logic.update_annotation(annotation, fields, True)

    for action in annotation['permissions']:
        assert user in annotation['permissions'][action]


@update_annotation_fixtures
def test_update_annotation_if_deleted_does_not_remove_other_principals():
    user = 'acct:fred@hypothes.is'
    annotation = _mock_annotation(
        deleted=True,
        user=user,
        permissions={
            'admin': [user, 'someone else'],
            'read': [user, 'someone else'],
            'update': [user],
            'delete': [user]
        }
    )
    fields = {
        'permissions': {
            'update': ['someone else'],
            'delete': ['someone else']
        }
    }

    logic.update_annotation(annotation, fields, True)

    for action in annotation['permissions']:
        assert 'someone else' in annotation['permissions'][action]


@update_annotation_fixtures
def test_update_annotation_calls_prepare(search_lib):
    annotation = _mock_annotation()

    logic.update_annotation(annotation, {}, False)

    search_lib.prepare.assert_called_once_with(annotation)


@update_annotation_fixtures
def test_update_annotation_calls_save():
    annotation = _mock_annotation()

    logic.update_annotation(annotation, {}, False)

    annotation.save.assert_called_once_with()


@update_annotation_fixtures
def test_update_annotation_does_not_crash_if_annotation_has_no_group():
    annotation = _mock_annotation()
    assert 'group' not in annotation

    logic.update_annotation(annotation, {}, False)


@update_annotation_fixtures
def test_update_annotation_does_not_crash_if_annotations_parent_has_no_group(
        Annotation):
    """It shouldn't crash if the parent annotation has no group.

    It shouldn't crash if the annotation is a reply and its parent annotation
    has no 'group' field.

    """
    # No group in the original annotation/reply itself.
    annotation = _mock_annotation()
    assert 'group' not in annotation

    # And no group in the parent annotation either.
    Annotation.fetch.return_value = {}

    logic.update_annotation(annotation, {}, False)


# The fixtures required to mock all of delete_annotation()'s dependencies.
delete_annotation_fixtures = pytest.mark.usefixtures()


@delete_annotation_fixtures
def test_delete_does_not_crash_if_annotation_has_no_group():
    annotation = mock.MagicMock()
    annotation_data = {}  # No 'group' key.
    annotation.get.side_effect = annotation_data.get
    annotation.__getitem__.side_effect = annotation_data.__getitem__

    logic.delete_annotation(annotation)


@delete_annotation_fixtures
def test_delete_annotation_calls_delete():
    annotation = mock.MagicMock()

    logic.delete_annotation(annotation)

    annotation.delete.assert_called_once_with()


@pytest.fixture
def Annotation(request):
    patcher = mock.patch('h.api.logic.Annotation', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def search_lib(request):
    patcher = mock.patch('h.api.logic.search_lib', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()

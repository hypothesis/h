import pytest
import mock

from h.api.groups import logic


def _mock_annotation(**kwargs):
    """Return a mock h.api.models.Annotation object."""
    annotation = mock.MagicMock()
    annotation.__getitem__.side_effect = kwargs.__getitem__
    annotation.__setitem__.side_effect = kwargs.__setitem__
    annotation.__delitem__.side_effect = kwargs.__delitem__
    annotation.__contains__.side_effect = kwargs.__contains__
    annotation.get.side_effect = kwargs.get
    annotation.update.side_effect = kwargs.update
    annotation.pop.side_effect = kwargs.pop
    return annotation


# The fixtures required to mock all of set_group_if_reply()'s dependencies.
set_group_if_reply_fixtures = pytest.mark.usefixtures('models')


@set_group_if_reply_fixtures
def test_set_group_if_reply_does_not_modify_non_replies():
    # This annotation is not a reply.
    annotation = _mock_annotation(group='test-group')

    logic.set_group_if_reply(annotation)

    assert annotation['group'] == 'test-group'


@set_group_if_reply_fixtures
def test_set_group_if_reply_calls_fetch_if_reply(models):
    """If the annotation is a reply it should call Annotation.fetch() once.

    And pass the parent ID.

    """
    annotation = _mock_annotation(references=['parent_id'])

    logic.set_group_if_reply(annotation)

    models.Annotation.fetch.assert_called_once_with('parent_id')


@set_group_if_reply_fixtures
def test_set_group_if_reply_adds_group_to_replies(models):
    """If a reply has no group it gets the group of its parent annotation."""
    annotation = _mock_annotation(references=['parent_id'])
    assert 'group' not in annotation

    # The parent annotation.
    models.Annotation.fetch.return_value = {'group': "parent_group"}

    logic.set_group_if_reply(annotation)

    assert annotation['group'] == "parent_group"


@set_group_if_reply_fixtures
def test_set_group_if_reply_overwrites_groups_in_replies(models):
    """If a reply has a group it's overwritten with the parent's group."""
    annotation = _mock_annotation(
        group='this should be overwritten',
        references=['parent_id'])

    # The parent annotation.
    models.Annotation.fetch.return_value = {'group': "parent_group"}

    logic.set_group_if_reply(annotation)

    assert annotation['group'] == "parent_group"


@set_group_if_reply_fixtures
def test_set_group_if_reply_clears_group_if_parent_has_no_group(models):
    annotation = _mock_annotation(
        group='this should be deleted',
        references=['parent_id'])

    # The parent annotation.
    models.Annotation.fetch.return_value = {}  # No 'group' key.

    logic.set_group_if_reply(annotation)

    assert 'group' not in annotation


@pytest.fixture
def models(request):
    patcher = mock.patch('h.api.groups.logic.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()

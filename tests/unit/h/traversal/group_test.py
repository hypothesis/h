from unittest.mock import sentinel

import pytest

from h.traversal.group import GroupRequiredRoot, GroupRoot


@pytest.mark.usefixtures("group_service", "GroupContext")
class TestGroupRoot:
    def test_it_returns_the_context_from_looking_up_the_group(
        self, pyramid_request, group_service, GroupContext
    ):
        root = GroupRoot(pyramid_request)

        context = root[sentinel.group_id]

        group_service.fetch.assert_called_once_with(sentinel.group_id)
        GroupContext.assert_called_once_with(group_service.fetch.return_value)

        assert context == GroupContext.return_value


@pytest.mark.usefixtures("group_service")
class TestGroupRequiredRoot:
    def test_getitem_returns_fetched_groupcontext_if_not_None(
        self, factories, pyramid_request, GroupContext
    ):
        GroupContext.return_value.group = factories.Group()

        context = GroupRequiredRoot(pyramid_request)[sentinel.group_id]

        assert context == GroupContext.return_value

    def test_getitem_raises_KeyError_if_there_is_no_group(
        self, pyramid_request, GroupContext
    ):
        GroupContext.return_value.group = None
        with pytest.raises(KeyError):
            _ = GroupRequiredRoot(pyramid_request)["does_not_exist"]


@pytest.fixture
def GroupContext(patch):
    return patch("h.traversal.group.GroupContext")

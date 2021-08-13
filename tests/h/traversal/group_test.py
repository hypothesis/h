from unittest.mock import sentinel

import pytest

from h.traversal.group import GroupContext, GroupRequiredRoot, GroupRoot


class TestGroupContext:
    def test_it_with_a_group(self, factories, ACL):
        group = factories.Group()

        context = GroupContext(group=group)

        assert context.group == group
        assert context.__acl__() == ACL.for_group.return_value
        ACL.for_group.assert_called_once_with(group)


@pytest.mark.usefixtures("group_service", "GroupContext_")
class TestGroupRoot:
    def test_it_passes_on_acls(self, pyramid_request, ACL):
        context = GroupRoot(pyramid_request)

        acls = context.__acl__()

        ACL.for_group.assert_called_once_with()
        assert acls == ACL.for_group.return_value

    def test_it_returns_the_context_from_looking_up_the_group(
        self, pyramid_request, group_service, GroupContext_
    ):
        root = GroupRoot(pyramid_request)

        context = root[sentinel.group_id]

        group_service.fetch.assert_called_once_with(sentinel.group_id)
        GroupContext_.assert_called_once_with(group_service.fetch.return_value)

        assert context == GroupContext_.return_value


@pytest.mark.usefixtures("group_service")
class TestGroupRequiredRoot:
    def test_getitem_returns_fetched_groupcontext_if_not_None(
        self, factories, pyramid_request, GroupContext_
    ):
        GroupContext_.return_value.group = factories.Group()

        context = GroupRequiredRoot(pyramid_request)[sentinel.group_id]

        assert context == GroupContext_.return_value

    def test_getitem_raises_KeyError_if_there_is_no_group(
        self, pyramid_request, GroupContext_
    ):
        GroupContext_.return_value.group = None
        with pytest.raises(KeyError):
            _ = GroupRequiredRoot(pyramid_request)["does_not_exist"]


@pytest.fixture
def ACL(patch):
    return patch("h.traversal.group.ACL")


@pytest.fixture
def GroupContext_(patch):
    return patch("h.traversal.group.GroupContext")

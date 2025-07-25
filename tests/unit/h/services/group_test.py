import datetime
from unittest import mock

import pytest

from h.models import Group, GroupMembership
from h.models.group import ReadableBy
from h.services.group import GroupService, groups_factory


class TestGroupServiceFetch:
    def test_it_proxies_to_fetch_by_groupid_if_groupid_valid(self, svc):
        svc.fetch_by_groupid = mock.Mock()

        result = svc.fetch("group:something@somewhere.com")

        svc.fetch_by_groupid.assert_called_once_with("group:something@somewhere.com")
        assert result == svc.fetch_by_groupid.return_value

    def test_it_proxies_to_fetch_by_pubid_if_not_groupid_syntax(self, svc):
        svc.fetch_by_pubid = mock.Mock()

        result = svc.fetch("abcdppp")

        svc.fetch_by_pubid.assert_called_once_with("abcdppp")
        assert result == svc.fetch_by_pubid.return_value


class TestGroupServiceFetchByPubid:
    def test_it_returns_group_model(self, svc, factories):
        group = factories.Group()

        fetched_group = svc.fetch_by_pubid(group.pubid)

        assert fetched_group == group
        assert isinstance(fetched_group, Group)

    def test_it_returns_None_if_no_group_found(self, svc):
        group = svc.fetch_by_pubid("abcdeff")

        assert group is None


class TestGroupServiceFetchByGroupid:
    def test_it_returns_group_model_of_matching_group(self, svc, factories):
        group = factories.Group(authority_provided_id="dingdong", authority="foo.com")

        fetched_group = svc.fetch_by_groupid(group.groupid)

        assert isinstance(fetched_group, Group)

    def test_it_raises_ValueError_if_invalid_groupid(self, svc):
        with pytest.raises(ValueError, match="isn't a valid groupid"):
            svc.fetch_by_groupid("fiddlesticks")

    def test_it_returns_None_if_no_matching_group(self, svc):
        assert svc.fetch_by_groupid("group:rando@dando.com") is None


@pytest.mark.usefixtures("groups")
class TestFilterByName:
    def test_it_filters_by_name(self, svc, matchers):
        filtered_groups = svc.filter_by_name(name="Hello")

        assert len(filtered_groups.all()) == 1
        assert filtered_groups.all() == [matchers.InstanceOf(Group, name="Hello")]

    def test_it_returns_all_groups_if_name_is_None(self, svc, groups):
        filtered_groups = svc.filter_by_name()

        # results include public group in addition to ``groups``
        assert len(filtered_groups.all()) == len(groups) + 1

    def test_it_is_case_insensitive(self, svc):
        filtered_groups = svc.filter_by_name(name="Amber")

        assert len(filtered_groups.all()) == 2

    def test_it_performs_wildcard_search(self, svc):
        filtered_groups = svc.filter_by_name(name="Finger")

        assert len(filtered_groups.all()) == 2

    def test_results_sorted_by_created_desc(self, svc, matchers):
        filtered_groups = svc.filter_by_name("Finger")

        assert filtered_groups.all() == [
            matchers.InstanceOf(Group, name="Fingers"),
            matchers.InstanceOf(Group, name="Finger"),
        ]

    @pytest.fixture
    def groups(self, factories):
        return [
            factories.Group(name="Finger", created=datetime.datetime(2015, 8, 2)),  # noqa: DTZ001
            factories.Group(name="Fingers", created=datetime.datetime(2018, 2, 1)),  # noqa: DTZ001
            factories.Group(name="Hello"),
            factories.Group(name="Amber"),
            factories.Group(name="amber"),
        ]


class TestGroupServiceGroupIds:
    """
    Unit tests for methods related to group IDs.

    - :py:meth:`GroupService.groups_readable_by`
    - :py:meth:`GroupService.groupids_created_by`
    """

    @pytest.mark.parametrize("with_user", [True, False])
    def test_readable_by_includes_world(self, with_user, svc, db_session, factories):
        user = None
        if with_user:
            user = factories.User()
            db_session.flush()

        groups = svc.groups_readable_by(user)

        assert "__world__" in [g.pubid for g in groups]

    @pytest.mark.parametrize("with_user", [True, False])
    def test_readable_by_includes_world_readable_groups(
        self, with_user, svc, db_session, factories
    ):
        # group readable by members
        factories.Group(readable_by=ReadableBy.members)
        # group readable by everyone
        group = factories.Group(readable_by=ReadableBy.world)
        user = None
        if with_user:
            user = factories.User()
            db_session.flush()

        groups = svc.groups_readable_by(user)

        assert group in groups

    def test_readable_by_includes_memberships(self, svc, db_session, factories):
        user = factories.User()
        group = factories.Group(readable_by=ReadableBy.members)
        group.memberships.append(GroupMembership(user=user))
        db_session.flush()

        groups = svc.groups_readable_by(user)

        assert group in groups

    def test_readable_by_applies_filter(self, svc, db_session, factories):
        user = factories.User()
        factories.Group(
            readable_by=ReadableBy.world
        )  # Group that shouldn't be returned
        group = factories.Group(readable_by=ReadableBy.world)
        db_session.flush()

        groups = svc.groups_readable_by(user, group_ids=[group.pubid, "doesnotexist"])

        assert list(groups) == [group]

    def test_created_by_includes_created_groups(self, svc, factories):
        user = factories.User()
        group = factories.Group(creator=user)

        assert group.pubid in svc.groupids_created_by(user)

    def test_created_by_excludes_other_groups(self, svc, db_session, factories):
        user = factories.User()
        private_group = factories.Group()
        private_group.memberships.append(GroupMembership(user=user))
        factories.Group(readable_by=ReadableBy.world)
        db_session.flush()

        assert svc.groupids_created_by(user) == []

    def test_created_by_returns_empty_list_for_missing_user(self, svc):
        assert svc.groupids_created_by(None) == []


@pytest.mark.usefixtures("user_service")
class TestGroupsFactory:
    def test_returns_groups_service(self, pyramid_request):
        svc = groups_factory(None, pyramid_request)

        assert isinstance(svc, GroupService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = groups_factory(None, pyramid_request)

        assert svc.session == pyramid_request.db

    def test_wraps_user_service_as_user_fetcher(self, pyramid_request, user_service):
        svc = groups_factory(None, pyramid_request)

        svc.user_fetcher("foo")

        user_service.fetch.assert_called_once_with("foo")


@pytest.fixture
def svc(db_session, user_service):
    return GroupService(db_session, user_service)

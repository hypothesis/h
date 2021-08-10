from unittest import mock

import pytest
from h_matchers import Any

from h.models import Group, GroupScope, User
from h.models.group import JoinableBy, ReadableBy, WriteableBy
from h.services.group_create import GroupCreateService, group_create_factory
from tests.common.matchers import Matcher


class TestCreatePrivateGroup:
    def test_it_returns_group_model(self, creator, svc):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert isinstance(group, Group)

    def test_it_sets_group_name(self, creator, svc):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.name == "Anteater fans"

    def test_it_sets_group_authority(self, svc, creator, pyramid_request):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.authority == pyramid_request.default_authority

    def test_it_sets_group_authority_as_creator_authority(
        self, svc, creator, pyramid_request
    ):
        pyramid_request.default_authority = "some_other_authority"
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.authority == creator.authority

    def test_it_sets_group_creator(self, svc, creator):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.creator == creator

    def test_it_sets_description_when_present(self, svc, creator):
        group = svc.create_private_group(
            "Anteater fans", creator.userid, description="all about ant eaters"
        )

        assert group.description == "all about ant eaters"

    def test_it_skips_setting_description_when_missing(self, svc, creator):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.description is None

    def test_it_adds_group_creator_to_members(self, svc, creator):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert creator in group.members

    @pytest.mark.parametrize(
        "flag,expected_value",
        [
            ("joinable_by", JoinableBy.authority),
            ("readable_by", ReadableBy.members),
            ("writeable_by", WriteableBy.members),
        ],
    )
    def test_it_sets_access_flags(self, svc, creator, flag, expected_value):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert getattr(group, flag) == expected_value

    def test_it_creates_group_with_no_organization_by_default(self, creator, svc):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.organization is None

    def test_it_creates_group_with_specified_organization(
        self, factories, creator, svc
    ):
        org = factories.Organization()

        group = svc.create_private_group(
            "Anteater fans", creator.userid, organization=org
        )

        assert group.organization == org

    def test_it_creates_group_with_enforce_scope_True_by_default(self, creator, svc):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.enforce_scope is True

    def test_it_sets_group_with_specified_enforce_scope(self, creator, svc):
        group = svc.create_private_group(
            "Anteater fans", creator.userid, enforce_scope=False
        )

        assert not group.enforce_scope

    def test_it_adds_group_to_session(self, db_session, creator, svc):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group in db_session

    def test_it_sets_group_ids(self, creator, svc):
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.id
        assert group.pubid

    def test_it_publishes_join_event(self, svc, creator, publish):
        group = svc.create_private_group("Dishwasher disassemblers", creator.userid)

        publish.assert_called_once_with("group-join", group.pubid, creator.userid)


class TestCreateOpenGroup:
    def test_it_returns_group_model(self, creator, svc, origins):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert isinstance(group, Group)

    @pytest.mark.parametrize(
        "group_attr,expected_value",
        [("name", "test group"), ("description", "test description")],
    )
    def test_it_creates_group_attrs(
        self, creator, svc, origins, group_attr, expected_value
    ):
        group = svc.create_open_group(
            "test group", creator.userid, scopes=origins, description="test description"
        )

        assert getattr(group, group_attr) == expected_value

    def test_it_sets_group_authority_as_creator_authority(
        self, svc, creator, pyramid_request
    ):
        pyramid_request.default_authority = "some_other_authority"
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.authority == creator.authority

    def test_it_skips_setting_description_when_missing(self, svc, creator, origins):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert group.description is None

    def test_it_sets_group_creator(self, svc, creator, origins):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert group.creator == creator

    def test_it_does_not_add_group_creator_to_members(self, svc, creator, origins):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert creator not in group.members

    @pytest.mark.parametrize(
        "flag,expected_value",
        [
            ("joinable_by", None),
            ("readable_by", ReadableBy.world),
            ("writeable_by", WriteableBy.authority),
        ],
    )
    def test_it_sets_access_flags(self, svc, creator, origins, flag, expected_value):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert getattr(group, flag) == expected_value

    def test_it_creates_group_with_no_organization_by_default(
        self, creator, svc, origins
    ):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert group.organization is None

    def test_it_creates_group_with_specified_organization(
        self, factories, creator, svc, origins
    ):
        org = factories.Organization()

        group = svc.create_open_group(
            "Anteater fans", creator.userid, scopes=origins, organization=org
        )

        assert group.organization == org

    def test_it_creates_group_with_enforce_scope_True_by_default(
        self, creator, svc, origins, db_session
    ):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        db_session.flush()

        assert group.enforce_scope is True

    def test_it_creates_group_with_specified_enforce_scope(
        self, creator, svc, origins, db_session
    ):
        group = svc.create_open_group(
            "Anteater fans", creator.userid, scopes=origins, enforce_scope=False
        )

        db_session.flush()

        assert not group.enforce_scope

    def test_it_adds_group_to_session(self, db_session, creator, svc, origins):
        group = svc.create_open_group("Anteater fans", creator.userid, scopes=origins)

        assert group in db_session

    def test_it_does_not_publish_join_event(self, svc, creator, publish, origins):
        svc.create_open_group(
            "Dishwasher disassemblers", creator.userid, scopes=origins
        )

        publish.assert_not_called()

    def test_it_sets_scopes(self, svc, creator):
        origins = ["https://biopub.org", "http://example.com", "https://wikipedia.com"]

        group = svc.create_open_group(
            name="test_group", userid=creator.userid, scopes=origins
        )

        assert (
            group.scopes
            == Any.list.containing([GroupScopeWithOrigin(h) for h in origins]).only()
        )

    def test_it_always_creates_new_scopes(self, factories, svc, creator):
        # It always creates a new scope, even if a scope with the given origin
        # already exists (this is because a single scope can only belong to
        # one group, so the existing scope can't be reused with the new group).
        origins = ["https://biopub.org", "http://example.com"]
        scopes = [factories.GroupScope(scope=h) for h in origins]

        group = svc.create_open_group(
            name="test_group", userid=creator.userid, scopes=origins
        )
        for scope in scopes:
            assert scope not in group.scopes


class TestCreateRestrictedGroup:
    def test_it_returns_group_model(self, creator, svc, origins):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert isinstance(group, Group)

    @pytest.mark.parametrize(
        "group_attr,expected_value",
        [("name", "test group"), ("description", "test description")],
    )
    def test_it_creates_group_attrs(
        self, creator, svc, origins, group_attr, expected_value
    ):
        group = svc.create_restricted_group(
            "test group", creator.userid, scopes=origins, description="test description"
        )

        assert getattr(group, group_attr) == expected_value

    def test_it_sets_group_authority_as_creator_authority(
        self, svc, creator, pyramid_request
    ):
        pyramid_request.default_authority = "some_other_authority"
        group = svc.create_private_group("Anteater fans", creator.userid)

        assert group.authority == creator.authority

    def test_it_skips_setting_description_when_missing(self, svc, creator, origins):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert group.description is None

    def test_it_sets_group_creator(self, svc, creator, origins):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert group.creator == creator

    def test_it_adds_group_creator_to_members(self, svc, creator, origins):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert creator in group.members

    @pytest.mark.parametrize(
        "flag,expected_value",
        [
            ("joinable_by", None),
            ("readable_by", ReadableBy.world),
            ("writeable_by", WriteableBy.members),
        ],
    )
    def test_it_sets_access_flags(self, svc, creator, origins, flag, expected_value):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert getattr(group, flag) == expected_value

    def test_it_creates_group_with_no_organization_by_default(
        self, creator, svc, origins
    ):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert group.organization is None

    def test_it_creates_group_with_specified_organization(
        self, factories, creator, svc, origins
    ):
        org = factories.Organization()

        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins, organization=org
        )

        assert group.organization == org

    def test_it_creates_group_with_enforce_scope_True_by_default(
        self, creator, svc, origins, db_session
    ):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        db_session.flush()

        assert group.enforce_scope is True

    def test_it_creates_group_with_specified_enforce_scope(
        self, creator, svc, origins, db_session
    ):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins, enforce_scope=False
        )

        db_session.flush()

        assert not group.enforce_scope

    def test_it_adds_group_to_session(self, db_session, creator, svc, origins):
        group = svc.create_restricted_group(
            "Anteater fans", creator.userid, scopes=origins
        )

        assert group in db_session

    def test_it_publishes_join_event(self, svc, creator, publish, origins):
        group = svc.create_restricted_group(
            "Dishwasher disassemblers", creator.userid, scopes=origins
        )

        publish.assert_called_once_with("group-join", group.pubid, creator.userid)

    def test_it_sets_scopes(self, svc, creator):
        origins = ["https://biopub.org", "http://example.com", "https://wikipedia.com"]

        group = svc.create_restricted_group(
            name="test_group", userid=creator.userid, scopes=origins
        )

        assert (
            group.scopes
            == Any.list.containing([GroupScopeWithOrigin(h) for h in origins]).only()
        )

    def test_it_with_mismatched_authorities_raises_value_error(
        self, svc, origins, creator, factories
    ):
        org = factories.Organization(name="My organization", authority="bar.com")
        with pytest.raises(ValueError):
            svc.create_restricted_group(
                name="test_group",
                userid=creator.userid,
                scopes=origins,
                description="test_description",
                organization=org,
            )

    def test_it_always_creates_new_scopes(self, factories, svc, creator):
        # It always creates a new scope, even if a scope with the given origin
        # already exists (this is because a single scope can only belong to
        # one group, so the existing scope can't be reused with the new group).
        origins = ["https://biopub.org", "http://example.com"]
        scopes = [factories.GroupScope(scope=h) for h in origins]

        group = svc.create_restricted_group(
            name="test_group", userid=creator.userid, scopes=origins
        )

        for scope in scopes:
            assert scope not in group.scopes


@pytest.mark.usefixtures("user_service")
class TestGroupCreateFactory:
    def test_returns_group_create_service(self, pyramid_request):
        svc = group_create_factory(None, pyramid_request)

        assert isinstance(svc, GroupCreateService)

    def test_provides_request_db_as_session(self, pyramid_request):
        svc = group_create_factory(None, pyramid_request)

        assert svc.db == pyramid_request.db

    def test_wraps_user_service_as_user_fetcher(self, pyramid_request, user_service):
        svc = group_create_factory(None, pyramid_request)

        svc.user_fetcher("foo")

        user_service.fetch.assert_called_once_with("foo")

    def test_provides_realtime_publisher_as_publish(self, patch, pyramid_request):
        pyramid_request.realtime = mock.Mock(spec_set=["publish_user"])
        session = patch("h.services.group_create.session")
        svc = group_create_factory(None, pyramid_request)

        svc.publish("group-join", "abc123", "theresa")

        session.model.assert_called_once_with(pyramid_request)
        pyramid_request.realtime.publish_user.assert_called_once_with(
            {
                "type": "group-join",
                "session_model": session.model.return_value,
                "userid": "theresa",
                "group": "abc123",
            }
        )


@pytest.fixture
def usr_svc(db_session):
    def fetch(userid):
        # One doesn't want to couple to the user fetching service but
        # we do want to be able to fetch user models for internal
        # module behavior tests
        return db_session.query(User).filter_by(userid=userid).one_or_none()

    return fetch


@pytest.fixture
def origins():
    return ["http://example.com"]


@pytest.fixture
def publish():
    return mock.Mock(spec_set=[])


@pytest.fixture
def svc(db_session, usr_svc, publish):
    return GroupCreateService(db_session, usr_svc, publish=publish)


@pytest.fixture
def creator(factories):
    return factories.User(username="group_creator")


class GroupScopeWithOrigin(Matcher):
    """Matches any GroupScope with the given origin."""

    def __init__(self, origin):
        super().__init__(
            f"* any group with origin: {origin} *",
            lambda other: isinstance(other, GroupScope) and other.origin == origin,
        )

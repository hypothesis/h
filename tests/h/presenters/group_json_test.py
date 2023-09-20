from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.presenters.group_json import GroupJSONPresenter, GroupsJSONPresenter

pytestmark = [
    pytest.mark.xdist_group("elasticsearch"),
    pytest.mark.usefixtures("init_elasticsearch"),
]


@pytest.mark.usefixtures("group_links_service")
class TestGroupJSONPresenter:
    def test_it(self, factories, pyramid_request, group_links_service):
        group = factories.Group(
            name="My Group",
            pubid="mygroup",
            authority_provided_id="abc123",
            organization=factories.Organization(),
        )

        results = GroupJSONPresenter(group, pyramid_request).asdict()

        assert results == Any.dict.containing(
            {
                "name": "My Group",
                "id": "mygroup",
                "groupid": "group:abc123@example.com",
                "organization": group.organization.pubid,
                "links": group_links_service.get_all.return_value,
                "scoped": False,
            }
        )

    def test_private_group_asdict(self, present, factories):
        results = present(factories.Group())

        assert results["type"] == "private"
        assert not results["public"]

    def test_open_group_asdict(self, present, open_group):
        results = present(open_group)

        assert results["type"] == "open"
        assert results["public"]

    def test_open_scoped_group_asdict(self, present, open_group):
        results = present(open_group)

        assert results["scoped"]

    def test_it_does_not_contain_deprecated_url(
        self, present, open_group, group_links_service
    ):
        group_links_service.get_all.return_value = {"html": "foobar"}

        results = present(open_group)

        assert "url" not in results

    def test_it_sets_organization_None_if_group_has_no_organization(
        self, present, open_group
    ):
        open_group.organization = None

        results = present(open_group)

        assert results["organization"] is None

    def test_it_does_not_expand_by_default(self, present, open_group):
        results = present(open_group)

        assert results["organization"] == open_group.organization.pubid
        assert "scopes" not in results

    def test_it_expands_organizations(
        self, present, open_group, OrganizationJSONPresenter
    ):
        results = present(open_group, expand=["organization"])

        assert (
            results["organization"]
            == OrganizationJSONPresenter.return_value.asdict.return_value
        )

    def test_expanded_organizations_None_if_missing(self, present, open_group):
        open_group.organization = None

        results = present(open_group, expand=["organization"])

        assert results["organization"] is None

    def test_it_expands_scopes(self, present, open_group):
        open_group.enforce_scope = False

        result = present(open_group, expand=["scopes"])

        assert "scopes" in result
        assert not result["scopes"]["enforced"]
        assert set(result["scopes"]["uri_patterns"]) == {
            "http://foo.com/bar*",
            "https://foo.com/baz*",
        }

    @pytest.mark.parametrize("enforce_scope", (True, False))
    def test_with_no_scopes(self, present, open_group, enforce_scope):
        open_group.scopes = []
        open_group.enforce_scope = enforce_scope

        result = present(open_group, expand=["scopes"])

        assert result["scopes"]["uri_patterns"] == []
        # Even if the model is configured to enforce scope, de facto
        # it can't if there are no scopes
        assert not result["scopes"]["enforced"]

    def test_it_ignores_unrecognized_expands(self, present, open_group):
        present(open_group, expand=["foobars", "dingdong"])

    @pytest.fixture
    def present(self, pyramid_request):
        def present(group, expand=None):
            presenter = GroupJSONPresenter(group, pyramid_request)
            return presenter.asdict(expand=expand)

        return present

    @pytest.fixture
    def open_group(self, factories):
        return factories.OpenGroup(
            organization=factories.Organization(),
            enforce_scope=True,
            scopes=[
                factories.GroupScope(scope="http://foo.com/bar"),
                factories.GroupScope(scope="https://foo.com/baz"),
            ],
        )

    @pytest.fixture
    def OrganizationJSONPresenter(self, patch):
        return patch("h.presenters.group_json.OrganizationJSONPresenter")


@pytest.mark.usefixtures("group_links_service")
class TestGroupsJSONPresenter:
    def test_it(self, factories, pyramid_request, GroupJSONPresenter):
        group = factories.Group()
        presenter = GroupsJSONPresenter(groups=[group], request=pyramid_request)

        result = presenter.asdicts(expand=sentinel.expand)

        GroupJSONPresenter.assert_called_once_with(group, pyramid_request)
        GroupJSONPresenter.return_value.asdict.assert_called_once_with(
            expand=sentinel.expand
        )
        assert result == [GroupJSONPresenter.return_value.asdict.return_value]

    @pytest.fixture(autouse=True)
    def GroupJSONPresenter(self, patch):
        return patch("h.presenters.group_json.GroupJSONPresenter")

from unittest import mock

import pytest
from h_matchers import Any

from h.views.admin import groups


@pytest.mark.usefixtures("group_service")
class TestIndex:
    def test_it_paginates_results(self, pyramid_request, paginate):
        groups.groups_index(None, pyramid_request)

        paginate.assert_called_once_with(pyramid_request, Any(), Any())

    def test_it_filters_groups_with_name_param(self, pyramid_request, group_service):
        pyramid_request.params["q"] = "fingers"

        groups.groups_index(None, pyramid_request)

        group_service.filter_by_name.assert_called_once_with(name="fingers")

    @pytest.fixture
    def paginate(self, patch):
        return patch("h.views.admin.groups.paginator.paginate")


@pytest.fixture
def authority():
    return "foo.com"


@pytest.fixture
def pyramid_request(pyramid_request, factories, authority):
    pyramid_request.session = mock.Mock(spec_set=["flash", "get_csrf_token"])
    pyramid_request.user = factories.User(authority=authority)
    return pyramid_request

from __future__ import unicode_literals

import colander
import pytest

from h.schemas.admin_organization import OrganizationSchema


class TestOrganizationSchema(object):
    def test_it_allows_valid_data(self, org_data, bound_schema):
        bound_schema.deserialize(org_data)

    @pytest.mark.parametrize(
        "invalid_logo", ["not an svg", "<svg>{}</svg>".format("a" * 20000)]  # Too long
    )
    def test_it_raises_if_logo_is_invalid(self, org_data, bound_schema, invalid_logo):
        org_data["logo"] = invalid_logo

        with pytest.raises(colander.Invalid):
            bound_schema.deserialize(org_data)

    @pytest.mark.parametrize(
        "invalid_name",
        ["What Are You Looking At Shenzhen Technology Company"],  # Too long
    )
    def test_it_raises_if_name_is_invalid(self, org_data, bound_schema, invalid_name):
        org_data["name"] = invalid_name

        with pytest.raises(colander.Invalid):
            bound_schema.deserialize(org_data)

    @pytest.fixture
    def org_data(self):
        return {
            "name": "Org name",
            "authority": "example.com",
            "logo": "<svg>foo</svg>",
        }

    @pytest.fixture
    def bound_schema(self, pyramid_csrf_request):
        return OrganizationSchema().bind(request=pyramid_csrf_request)

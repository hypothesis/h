from __future__ import unicode_literals

import colander
import pytest

from h.schemas.forms.admin.organization import (
    OrganizationSchema,
    ORGANIZATION_LOGO_MAX_CHARS,
)


class TestOrganizationSchema(object):
    def test_it_allows_valid_data(self, org_data, bound_schema):
        bound_schema.deserialize(org_data)

    def test_it_raises_if_logo_is_too_long(self, org_data, bound_schema):
        org_data["logo"] = '<svg xmlns="http://svg.com">{}</svg>'.format(
            "a" * ORGANIZATION_LOGO_MAX_CHARS + "b"
        )

        with pytest.raises(
            colander.Invalid,
            match="larger than {:,d} characters".format(ORGANIZATION_LOGO_MAX_CHARS),
        ):
            bound_schema.deserialize(org_data)

    def test_it_raises_if_logo_is_malformed(self, org_data, bound_schema):
        org_data["logo"] = "<svg> oopsy </s>"

        with pytest.raises(colander.Invalid, match="not parsable XML"):
            bound_schema.deserialize(org_data)

    def test_it_raises_if_logo_is_not_svg(self, org_data, bound_schema):
        org_data["logo"] = "<h>This is not a svg</h>"

        with pytest.raises(colander.Invalid, match="does not start with <svg> tag"):
            bound_schema.deserialize(org_data)

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "What Are You Looking At Shenzhen Technology Company",  # Too long
            "",  # Too short
        ],
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

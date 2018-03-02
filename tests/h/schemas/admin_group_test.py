# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import colander
import pytest

from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH
)
from h.schemas.admin_group import CreateAdminGroupSchema


class TestCreateGroupSchema(object):

    def test_it_allows_with_valid_data(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_raises_if_name_too_short(self, group_data, bound_schema):
        too_short_name = 'a' * (GROUP_NAME_MIN_LENGTH - 1)
        group_data['name'] = too_short_name
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('name') >= 0

    def test_it_raises_if_name_too_long(self, group_data, bound_schema):
        too_long_name = 'a' * (GROUP_NAME_MAX_LENGTH + 1)
        group_data['name'] = too_long_name
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('name') >= 0

    def test_it_raises_if_description_too_long(self, group_data, bound_schema):
        too_long_description = 'a' * (GROUP_DESCRIPTION_MAX_LENGTH + 1)
        group_data['description'] = too_long_description

        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('description') >= 0

    @pytest.mark.parametrize('required_field', (
        'name',
        'authority',
        'group_type',
        'creator'
    ))
    def test_it_raises_if_required_field_missing(self, group_data, bound_schema, required_field):
        group_data.pop(required_field)
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find(required_field) >= 0

    def test_it_allows_when_optional_field_missing(self, group_data, bound_schema):
        group_data.pop('description')

        bound_schema.deserialize(group_data)


@pytest.fixture
def group_data(factories):
    return {
        'name': 'My Group',
        'authority': 'example.com',
        'group_type': 'open',
        'creator': factories.User().username,
        'description': 'Lorem ipsum dolor sit amet consectetuer',
    }


@pytest.fixture
def bound_schema(pyramid_csrf_request):
    schema = CreateAdminGroupSchema().bind(request=pyramid_csrf_request)
    return schema

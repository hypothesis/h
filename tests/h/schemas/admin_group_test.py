# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import colander
import pytest

from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
)
from h.schemas.admin_group import CreateAdminGroupSchema


class TestCreateGroupSchema(object):

    def test_it_raises_if_name_too_short(self, group_data, bound_schema):
        too_short_name = u'a' * (GROUP_NAME_MIN_LENGTH - 1)
        group_data['name'] = too_short_name
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('name') >= 0

    def test_it_raises_if_name_too_long(self, group_data, bound_schema):
        too_long_name = u'a' * (GROUP_NAME_MAX_LENGTH + 1)
        group_data['name'] = too_long_name
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('name') >= 0

    def test_it_raises_if_name_missing(self, group_data, bound_schema):
        group_data.pop('name')
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('name') >= 0

    def test_it_raises_if_authority_missing(self, group_data, bound_schema):
        group_data.pop('authority')
        with pytest.raises(colander.Invalid) as exc:
            bound_schema.deserialize(group_data)

        assert str(exc.value).find('authority') >= 0


@pytest.fixture
def group_data():
    return {
        'name': u'My Group',
        'authority': u'example.com'
    }


@pytest.fixture
def bound_schema(pyramid_csrf_request):
    schema = CreateAdminGroupSchema().bind(request=pyramid_csrf_request)
    return schema

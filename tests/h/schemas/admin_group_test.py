# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import colander
import pytest
import mock

from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH
)
from h.schemas.admin_group import CreateAdminGroupSchema, user_exists_validator_factory
from h.services.user import UserService


class TestCreateGroupSchema(object):

    def test_it_allows_with_valid_data(self, group_data, bound_schema):
        bound_schema.deserialize(group_data)

    def test_it_raises_if_name_too_short(self, group_data, bound_schema):
        too_short_name = 'a' * (GROUP_NAME_MIN_LENGTH - 1)
        group_data['name'] = too_short_name

        with pytest.raises(colander.Invalid, match='.*name.*'):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_name_too_long(self, group_data, bound_schema):
        too_long_name = 'a' * (GROUP_NAME_MAX_LENGTH + 1)
        group_data['name'] = too_long_name

        with pytest.raises(colander.Invalid, match='.*name.*'):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_description_too_long(self, group_data, bound_schema):
        too_long_description = 'a' * (GROUP_DESCRIPTION_MAX_LENGTH + 1)
        group_data['description'] = too_long_description

        with pytest.raises(colander.Invalid, match='.*description.*'):
            bound_schema.deserialize(group_data)

    def test_it_raises_if_group_type_invalid(self, group_data, bound_schema):
        group_data['group_type'] = 'foobarbazding'

        with pytest.raises(colander.Invalid, match='.*group_type.*'):
            bound_schema.deserialize(group_data)

    @pytest.mark.parametrize('required_field', (
        'name',
        'authority',
        'group_type',
        'creator'
    ))
    def test_it_raises_if_required_field_missing(self, group_data, bound_schema, required_field):
        group_data.pop(required_field)

        with pytest.raises(colander.Invalid, match='.*{field}.*'.format(field=required_field)):
            bound_schema.deserialize(group_data)

    @pytest.mark.parametrize('optional_field', (
        'description',
        'origins'
    ))
    def test_it_allows_when_optional_field_missing(self, group_data, bound_schema, optional_field):
        group_data.pop(optional_field)

        bound_schema.deserialize(group_data)

    @pytest.mark.parametrize('input_origins,expected_origins', (
        ('http://www.foo.com', ['http://www.foo.com']),
        ('http://www.foo.com\r\nhttps://www.foo.com', ['http://www.foo.com', 'https://www.foo.com']),
        ('http://www.foo.com   ', ['http://www.foo.com']),
        ('http://www.foo.com\nhttps://www.foo.com', ['http://www.foo.com', 'https://www.foo.com']),
    ))
    def test_it_splits_origins_by_line(self, group_data, bound_schema, input_origins, expected_origins):
        group_data['origins'] = input_origins
        appstruct = bound_schema.deserialize(group_data)

        assert appstruct['origins'] == expected_origins


class TestCreateSchemaWithValidator(object):

    def test_it_passes_creator_and_authority_to_service(self,
                                                        group_data,
                                                        pyramid_csrf_request,
                                                        user_svc,
                                                        user_validator):
        schema = CreateAdminGroupSchema(validator=user_validator).bind(request=pyramid_csrf_request)
        schema.deserialize(group_data)

        user_svc.fetch.assert_called_with(group_data['creator'], group_data['authority'])

    def test_it_allows_when_user_exists_at_authority(self,
                                                     group_data,
                                                     pyramid_csrf_request,
                                                     user_svc,
                                                     user_validator):
        schema = CreateAdminGroupSchema(validator=user_validator).bind(request=pyramid_csrf_request)
        schema.deserialize(group_data)

    def test_it_raises_when_user_not_found(self,
                                           group_data,
                                           pyramid_csrf_request,
                                           user_svc,
                                           user_validator):
        user_svc.fetch.return_value = None
        schema = CreateAdminGroupSchema(validator=user_validator).bind(request=pyramid_csrf_request)

        with pytest.raises(colander.Invalid, match='.*creator.*'):
            schema.deserialize(group_data)

    @pytest.fixture
    def user_svc(self):
        svc = mock.create_autospec(UserService, spec_set=True, instance=True)
        return svc

    @pytest.fixture
    def user_validator(self, user_svc):
        validator = user_exists_validator_factory(user_svc)
        return validator


@pytest.fixture
def group_data(factories):
    return {
        'name': 'My Group',
        'authority': 'example.com',
        'group_type': 'open',
        'creator': factories.User().username,
        'description': 'Lorem ipsum dolor sit amet consectetuer',
        'origins': 'http://www.foo.com\r\nhttps://www.foo.com'
    }


@pytest.fixture
def bound_schema(pyramid_csrf_request):
    schema = CreateAdminGroupSchema().bind(request=pyramid_csrf_request)
    return schema

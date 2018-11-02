# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
    GROUP_DESCRIPTION_MAX_LENGTH,
    AUTHORITY_PROVIDED_ID_MAX_LENGTH,
)

from h.schemas.api.group import CreateGroupAPISchema
from h.schemas import ValidationError


class TestCreateGroupSchema(object):

    def test_it_raises_if_name_missing(self):
        schema = CreateGroupAPISchema()
        with pytest.raises(ValidationError, match=".*is a required property.*"):
            schema.validate({})

    def test_it_raises_if_name_too_short(self):
        schema = CreateGroupAPISchema()
        with pytest.raises(ValidationError) as exc:
            schema.validate({
                'name': 'o' * (GROUP_NAME_MIN_LENGTH - 1)
            })
        assert "name:" in str(exc.value)
        assert "is too short" in str(exc.value)

    def test_it_raises_if_name_too_long(self):
        schema = CreateGroupAPISchema()
        with pytest.raises(ValidationError) as exc:
            schema.validate({
                'name': 'o' * (GROUP_NAME_MAX_LENGTH + 1)
            })
        assert "name:" in str(exc.value)
        assert "is too long" in str(exc.value)

    def test_it_validates_with_valid_name(self):
        schema = CreateGroupAPISchema()

        appstruct = schema.validate({
            'name': 'Perfectly Fine'
        })

        assert 'name' in appstruct

    def test_it_validates_with_valid_description(self):
        schema = CreateGroupAPISchema()

        appstruct = schema.validate({
            'name': 'This Seems Fine',
            'description': 'This description seems adequate'
        })

        assert 'description' in appstruct

    def test_it_raises_if_description_too_long(self):
        schema = CreateGroupAPISchema()
        with pytest.raises(ValidationError) as exc:
            schema.validate({
                'name': 'Name not the Problem',
                'description': 'o' * (GROUP_DESCRIPTION_MAX_LENGTH + 1)
            })
        assert "description:" in str(exc.value)
        assert "is too long" in str(exc.value)

    def test_it_validates_with_valid_groupid(self):
        schema = CreateGroupAPISchema()

        appstruct = schema.validate({
            'name': 'This Seems Fine',
            'groupid': 'group:1234abcd!~*()@thirdparty.com',
        })

        assert 'groupid' in appstruct

    def test_it_raises_if_groupid_too_long(self):
        schema = CreateGroupAPISchema()

        with pytest.raises(ValidationError) as exc:
            schema.validate({
                'name': 'Name not the Problem',
                'groupid': 'group:' + ('o' * (AUTHORITY_PROVIDED_ID_MAX_LENGTH + 1)) + '@foobar.com'
            })

        assert "groupid:" in str(exc.value)
        # Because of the complexity of ``groupid`` formatting, the length of the
        # ``authority_provided_id`` segment of it is defined in the pattern for
        # valid ``groupid``s — not as a length constraint
        assert "does not match" in str(exc.value)

    def test_it_raises_if_groupid_has_invalid_chars(self):
        schema = CreateGroupAPISchema()

        with pytest.raises(ValidationError) as exc:
            schema.validate({
                'name': 'Name not the Problem',
                'groupid': 'group:&&?@thirdparty.com'
            })

        assert "groupid:" in str(exc.value)
        assert "does not match" in str(exc.value)

    def test_validate_groupid_does_not_raise_on_groupid_if_third_party(self, appstruct):
        CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                              group_authority='thirdparty.com',
                                              default_authority='hypothes.is')

    def test_validate_groupid_does_not_raise_when_groupid_is_None(self, appstruct):
        appstruct['groupid'] = None

        CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                              group_authority='hypothes.is',
                                              default_authority='hypothes.is')

    def test_validate_groupid_raises_ValidationError_if_first_party(self, appstruct):
        with pytest.raises(ValidationError, match="groupid may only be set on groups oustide of the default authority"):
            CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                                  group_authority='hypothes.is',
                                                  default_authority='hypothes.is')

    def test_validate_groupid_raises_ValidationError_if_no_group_authority(self, appstruct):
        with pytest.raises(ValidationError, match="groupid may only be set on groups oustide of the default authority"):
            CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                                  group_authority=None,
                                                  default_authority='hypothes.is')

    def test_validate_groupid_raises_ValidationError_groupid_format_invalid(self, appstruct):
        appstruct['groupid'] = 'group:++{{":}"}}@thirdparty.com'
        with pytest.raises(ValidationError, match="does not match valid groupid format"):
            CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                                  group_authority='thirdparty.com',
                                                  default_authority='hypothes.is')

    def test_validate_groupid_raises_ValidationError_groupid_authority_mismatch(self, appstruct):
        appstruct['groupid'] = 'group:valid_id@invalidauthority.com'
        with pytest.raises(ValidationError, match="Invalid authority.*in groupid"):
            CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                                  group_authority='thirdparty.com',
                                                  default_authority='hypothes.is')

    def test_validate_groupid_returns_groupid_parts(self, appstruct):
        appstruct['groupid'] = 'group:hullo@thirdparty.com'

        parts = CreateGroupAPISchema.validate_groupid(appstruct=appstruct,
                                                      group_authority='thirdparty.com',
                                                      default_authority='hypothes.is')

        assert 'authority_provided_id' in parts
        assert 'authority' in parts
        assert parts['authority_provided_id'] == 'hullo'
        assert parts['authority'] == 'thirdparty.com'

    @pytest.fixture
    def appstruct(self):
        return {
            'groupid': 'group:valid_id@thirdparty.com',
            'name': 'DingDong!',
            'description': 'OH, hello there',
        }

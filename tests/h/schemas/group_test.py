# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
# import mock

from h.models.group import (
    GROUP_NAME_MIN_LENGTH,
    GROUP_NAME_MAX_LENGTH,
)

from h.schemas.group import CreateGroupAPISchema
from h.schemas import ValidationError


class TestCreateGroupSchema(object):

    def test_it_raises_if_name_missing(self):
        schema = CreateGroupAPISchema()
        with pytest.raises(ValidationError) as exc:
            schema.validate({})

        # The substring tests here an in following tests are to get
        # around the occasional literal "u" prefix in Py2 err values
        assert "is a required property" in str(exc.value)

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

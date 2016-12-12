# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from memex import auth


@pytest.mark.parametrize('groupid', [
    '__world__',
    'foobar',
    '',
    None,
])
def test_group_write_permitted_returns_true(pyramid_request, groupid):
    assert auth.group_write_permitted(pyramid_request, groupid) is True

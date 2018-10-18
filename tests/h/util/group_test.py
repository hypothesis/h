# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.util import group as group_util


class TestSplitGroupID(object):
    @pytest.mark.parametrize('groupid,authority_provided_id,authority', [
        ('group:flashbang@dingdong.com', 'flashbang', 'dingdong.com'),
        ('group::ffff@dingdong.com', ':ffff', 'dingdong.com'),
        ('group:\\f!orklift@sprongle.co', '\\f!orklift', 'sprongle.co'),
        ('group:.@dingdong.com', '.', 'dingdong.com'),
        ('group:group:@yep.nope', 'group:', 'yep.nope'),
        ('group:()@hi.co', '()', 'hi.co'),
        ("group:!.~--_*'@hi.co", "!.~--_*'", 'hi.co'),
        ])
    def test_it_splits_valid_groupids(self, groupid, authority_provided_id, authority):
        splitgroup = group_util.split_groupid(groupid)

        assert splitgroup['authority_provided_id'] == authority_provided_id
        assert splitgroup['authority'] == authority

    @pytest.mark.parametrize('groupid', [
        'groupp:whatnot@dingdong.co',
        'grou:whatnot@dingdong.co',
        'group:@dingdog.com',
        'group:@',
        'whatnot@dingdong.co',
        'group:@@dingdong.com',
    ])
    def test_it_raises_ValueError_on_invalid_groupids(self, groupid):
        with pytest.raises(ValueError, match='valid groupid'):
            group_util.split_groupid(groupid)

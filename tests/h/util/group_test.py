import pytest

from h.util import group as group_util


class TestSplitGroupID:
    @pytest.mark.parametrize(
        "groupid,authority_provided_id,authority",
        [
            ("group:flashbang@dingdong.com", "flashbang", "dingdong.com"),
            ("group:ffff@dingdong.com", "ffff", "dingdong.com"),
            ("group:.@dingdong.com", ".", "dingdong.com"),
            ("group:group@yep.nope", "group", "yep.nope"),
            ("group:()@hi.co", "()", "hi.co"),
            ("group:!.~--_*'@hi.co", "!.~--_*'", "hi.co"),
        ],
    )
    def test_it_splits_valid_groupids(self, groupid, authority_provided_id, authority):
        splitgroup = group_util.split_groupid(groupid)

        assert splitgroup["authority_provided_id"] == authority_provided_id
        assert splitgroup["authority"] == authority

    @pytest.mark.parametrize(
        "groupid",
        [
            "groupp:whatnot@dingdong.co",
            "grou:whatnot@dingdong.co",
            "group:@dingdog.com",
            "group:@",
            "whatnot@dingdong.co",
            "group:@@dingdong.com",
            "group:\\f!orklift@sprongle.co",
            "group:another:@ding.com",
        ],
    )
    def test_it_raises_ValueError_on_invalid_groupids(self, groupid):
        with pytest.raises(ValueError, match="valid groupid"):
            group_util.split_groupid(groupid)


class TestIsGroupid:
    @pytest.mark.parametrize(
        "maybe_groupid,result",
        [
            ("group:flashbang@dingdong.com", True),
            ("group::ffff@dingdong.com", False),
            ("group:\\f!orklift@sprongle.co", False),
            ("group:.@dingdong.com", True),
            ("group:group@yep.nope", True),
            ("group:()@hi.co", True),
            ("group:!.~--_*'@hi.co", True),
            ("groupp:whatnot@dingdong.co", False),
            ("grou:whatnot@dingdong.co", False),
            ("group:@dingdog.com", False),
            ("group:@", False),
            ("whatnot@dingdong.co", False),
            ("group:@@dingdong.com", False),
        ],
    )
    def test_it_detects_groupid_validity(self, maybe_groupid, result):
        assert group_util.is_groupid(maybe_groupid) is result

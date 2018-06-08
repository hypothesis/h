# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

import colander

from h.groups import schemas


class TestUnblacklistedGroupNameSlug(object):
    @pytest.mark.parametrize(
        "group_name",
        [
            "edit",
            "edIT-",
            "EDit__",
            "EDIT-------",
            "eDiT?",
            "leave",
            "leAVE-",
            "LEAve_",
            "LEAVE---",
            "LeAvE???",
        ],
    )
    def test_blacklisted(self, dummy_node, group_name):
        blacklist = set(["edit", "leave"])

        with pytest.raises(colander.Invalid):
            schemas.unblacklisted_group_name_slug(dummy_node, group_name, blacklist)

    @pytest.mark.parametrize(
        "group_name",
        ["Birdwatchers", "My Book Club", "Hello World", "Editors", "Leavers"],
    )
    def test_passing(self, dummy_node, group_name):
        blacklist = set(["edit", "leave"])

        schemas.unblacklisted_group_name_slug(dummy_node, group_name, blacklist)

    @pytest.fixture
    def dummy_node(self, pyramid_request):
        class DummyNode(object):
            def __init__(self, request):
                self.bindings = {"request": request}

        return DummyNode(pyramid_request)

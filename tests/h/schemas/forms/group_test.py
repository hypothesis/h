# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

import colander

from h.schemas.forms.group import unblacklisted_group_name_slug


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
    def test_it_raises_if_group_name_is_blacklisted(self, dummy_node, group_name):
        with pytest.raises(colander.Invalid):
            unblacklisted_group_name_slug(dummy_node, group_name)

    @pytest.mark.parametrize(
        "group_name",
        ["Birdwatchers", "My Book Club", "Hello World", "Editors", "Leavers"],
    )
    def test_it_does_not_raise_if_group_name_is_not_blacklisted(
        self, dummy_node, group_name
    ):
        unblacklisted_group_name_slug(dummy_node, group_name)

    @pytest.fixture
    def dummy_node(self, pyramid_request):
        class DummyNode(object):
            def __init__(self, request):
                self.bindings = {"request": request}

        return DummyNode(pyramid_request)

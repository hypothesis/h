# -*- coding: utf-8 -*-
from collections import namedtuple

import colander
from horus.interfaces import IUIStrings
from horus.strings import UIStringsBase
import pytest
from pyramid.testing import DummyRequest, testConfig
from six import StringIO

from h.auth.local.schemas import unblacklisted_username


DummyNode = namedtuple('DummyNode', ('bindings'))


def configure(config):
    config.registry.registerUtility(UIStringsBase, IUIStrings)


def test_unblacklisted_username():
    node = DummyNode({'request': DummyRequest()})

    blacklist = set(['admin', 'root', 'postmaster'])

    with testConfig() as config:
        configure(config)
        # Should not raise for valid usernames
        unblacklisted_username(node, "john", blacklist)
        unblacklisted_username(node, "Abigail", blacklist)
        # Should raise for usernames in blacklist
        pytest.raises(colander.Invalid,
                      unblacklisted_username,
                      node,
                      "admin",
                      blacklist)
        # Should raise for case variants of usernames in blacklist
        pytest.raises(colander.Invalid,
                      unblacklisted_username,
                      node,
                      "PostMaster",
                      blacklist)

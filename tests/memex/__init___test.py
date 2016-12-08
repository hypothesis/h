# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock

import memex


def test_set_groupfinder(pyramid_config):
    memex.set_groupfinder(pyramid_config, mock.sentinel.groupfinder)

    assert pyramid_config.registry[memex.GROUPFINDER_KEY] == mock.sentinel.groupfinder


def test_set_groupfinder_resolves_dotted_path(pyramid_config):
    pyramid_config.maybe_dotted = mock.Mock()

    memex.set_groupfinder(pyramid_config, mock.sentinel.groupfinder)

    pyramid_config.maybe_dotted.assert_called_once_with(mock.sentinel.groupfinder)


def test_set_groupfinder_sets_dotted_path_resolved_object(pyramid_config):
    pyramid_config.maybe_dotted = mock.Mock()

    memex.set_groupfinder(pyramid_config, mock.sentinel.groupfinder)

    assert pyramid_config.registry[memex.GROUPFINDER_KEY] == pyramid_config.maybe_dotted.return_value

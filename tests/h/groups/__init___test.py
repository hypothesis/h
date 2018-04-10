# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

from h.groups import includeme
from h.groups.search import GroupAuthFilter


def test_includeme_registers_search_filter(pyramid_config):
    includeme(pyramid_config)
    assert GroupAuthFilter in pyramid_config.get_search_filters()


@pytest.fixture
def pyramid_config(pyramid_config):
    pyramid_config.add_directive('set_groupfinder', lambda c, f: None)

    filters = []
    pyramid_config.add_directive('add_search_filter',
                                 lambda c, f: filters.append(pyramid_config.maybe_dotted(f)))
    pyramid_config.add_directive('get_search_filters',
                                 lambda c: filters)
    return pyramid_config

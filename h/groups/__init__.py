# -*- coding: utf-8 -*-

from h.groups import search


def includeme(config):
    config.memex_set_groupfinder('h.groups.util.fetch_group')
    config.memex_add_search_filter(search.GroupAuthFilter)

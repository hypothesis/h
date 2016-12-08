# -*- coding: utf-8 -*-

from h.groups import util


def includeme(config):
    config.register_service_factory('.services.groups_factory', name='groups')
    config.memex_set_groupfinder('h.groups.util.fetch_group')

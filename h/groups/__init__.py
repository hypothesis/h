# -*- coding: utf-8 -*-

from h.groups.auth import annotation_group_write_permitted


def includeme(config):
    config.set_memex_group_write_permitted(annotation_group_write_permitted)

    config.register_service_factory('.services.groups_factory', name='groups')

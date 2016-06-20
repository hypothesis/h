# -*- coding: utf-8 -*-


def includeme(config):
    config.register_service_factory('.services.groups_factory', name='groups')

    config.include('.views')

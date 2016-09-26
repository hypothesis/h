# -*- coding: utf-8 -*-


def includeme(config):
    config.register_service_factory('.services.user.rename_user_factory', name='rename_user')

    config.include('.views')

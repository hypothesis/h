# -*- coding: utf-8 -*-

"""Service definitions that handle business logic."""

from __future__ import unicode_literals


def includeme(config):
    config.register_service_factory('.group.groups_factory', name='groups')
    config.register_service_factory('.nipsa.nipsa_factory', name='nipsa')
    config.register_service_factory('.settings.settings_factory', name='settings')
    config.register_service_factory('.user.user_service_factory', name='user')
    config.register_service_factory('.user_signup.user_signup_service_factory', name='user_signup')

# -*- coding: utf-8 -*-

"""Service definitions that handle business logic."""

from __future__ import unicode_literals


def includeme(config):
    config.register_service_factory('.annotation_stats.annotation_stats_factory', name='annotation_stats')
    config.register_service_factory('.auth_ticket.auth_ticket_service_factory',
                                    iface='pyramid_authsanity.interfaces.IAuthService')
    config.register_service_factory('.group.groups_factory', name='group')
    config.register_service_factory('.nipsa.nipsa_factory', name='nipsa')
    config.register_service_factory('.oauth.oauth_service_factory', name='oauth')
    config.register_service_factory('.rename_user.rename_user_factory', name='rename_user')
    config.register_service_factory('.settings.settings_factory', name='settings')
    config.register_service_factory('.user.user_service_factory', name='user')
    config.register_service_factory('.user_signup.user_signup_service_factory', name='user_signup')

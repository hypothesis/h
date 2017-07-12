# -*- coding: utf-8 -*-

"""Service definitions that handle business logic."""

from __future__ import unicode_literals


def includeme(config):
    config.register_service_factory('.annotation_json_presentation.annotation_json_presentation_service_factory',
                                    name='annotation_json_presentation')
    config.register_service_factory('.annotation_moderation.annotation_moderation_service_factory', name='annotation_moderation')
    config.register_service_factory('.annotation_stats.annotation_stats_factory', name='annotation_stats')
    config.register_service_factory('.auth_ticket.auth_ticket_service_factory',
                                    iface='pyramid_authsanity.interfaces.IAuthService')
    config.register_service_factory('.auth_token.auth_token_service_factory', name='auth_token')
    config.register_service_factory('.authority_group.authority_group_factory', name='authority_group')
    config.register_service_factory('.feature.feature_service_factory', name='feature')
    config.register_service_factory('.flag.flag_service_factory', name='flag')
    config.register_service_factory('.flag_count.flag_count_service_factory', name='flag_count')
    config.register_service_factory('.group.groups_factory', name='group')
    config.register_service_factory('.groupfinder.groupfinder_service_factory', iface='h.interfaces.IGroupService')
    config.register_service_factory('.links.links_factory', name='links')
    config.register_service_factory('.nipsa.nipsa_factory', name='nipsa')
    config.register_service_factory('.oauth.oauth_service_factory', name='oauth')
    config.register_service_factory('.oauth_validator.oauth_validator_service_factory', name='oauth_validator')
    config.register_service_factory('.rename_user.rename_user_factory', name='rename_user')
    config.register_service_factory('.settings.settings_factory', name='settings')
    config.register_service_factory('.user.user_service_factory', name='user')
    config.register_service_factory('.user_password.user_password_service_factory', name='user_password')
    config.register_service_factory('.user_signup.user_signup_service_factory', name='user_signup')

    config.add_directive('add_annotation_link_generator',
                         '.links.add_annotation_link_generator')
    config.add_request_method('.feature.FeatureRequestProperty',
                              name='feature',
                              reify=True)

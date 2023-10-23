"""Service definitions that handle business logic."""
from h.services.annotation_metadata import AnnotationMetadataService
from h.services.annotation_read import AnnotationReadService
from h.services.annotation_write import AnnotationWriteService
from h.services.auth_cookie import AuthCookieService
from h.services.bulk_api import BulkAnnotationService, BulkGroupService
from h.services.subscription import SubscriptionService


def includeme(config):  # pragma: no cover
    # Annotation related services
    config.register_service_factory(
        "h.services.annotation_delete.annotation_delete_service_factory",
        name="annotation_delete",
    )
    config.register_service_factory(
        "h.services.annotation_json.factory", name="annotation_json"
    )
    config.register_service_factory(
        "h.services.annotation_metadata.factory", iface=AnnotationMetadataService
    )
    config.register_service_factory(
        "h.services.annotation_moderation.annotation_moderation_service_factory",
        name="annotation_moderation",
    )
    config.register_service_factory(
        "h.services.annotation_read.service_factory", iface=AnnotationReadService
    )
    config.register_service_factory(
        "h.services.annotation_stats.annotation_stats_factory", name="annotation_stats"
    )
    config.register_service_factory(
        "h.services.annotation_write.service_factory", iface=AnnotationWriteService
    )

    # Other services
    config.register_service_factory(
        "h.services.auth_cookie.factory", iface=AuthCookieService
    )
    config.register_service_factory(
        "h.services.auth_token.auth_token_service_factory", name="auth_token"
    )
    config.register_service_factory(
        "h.services.bulk_api.annotation.service_factory", iface=BulkAnnotationService
    )
    config.register_service_factory(
        "h.services.bulk_api.group.service_factory", iface=BulkGroupService
    )
    config.register_service_factory(
        "h.services.developer_token.developer_token_service_factory",
        name="developer_token",
    )
    config.register_service_factory(
        "h.services.document.document_service_factory", name="document"
    )
    config.register_service_factory(
        "h.services.feature.feature_service_factory", name="feature"
    )
    config.register_service_factory("h.services.flag.flag_service_factory", name="flag")
    config.add_request_method(
        "h.services.feature.FeatureRequestProperty", name="feature", reify=True
    )

    # Group related services
    config.register_service_factory("h.services.group.groups_factory", name="group")
    config.register_service_factory(
        "h.services.group_delete.service_factory", name="group_delete"
    )
    config.register_service_factory(
        "h.services.group_create.group_create_factory", name="group_create"
    )
    config.register_service_factory(
        "h.services.group_links.group_links_factory", name="group_links"
    )
    config.register_service_factory(
        "h.services.group_list.group_list_factory", name="group_list"
    )
    config.register_service_factory(
        "h.services.group_members.group_members_factory", name="group_members"
    )
    config.register_service_factory(
        "h.services.group_scope.group_scope_factory", name="group_scope"
    )
    config.register_service_factory(
        "h.services.group_update.group_update_factory", name="group_update"
    )

    # Other services
    config.add_directive(
        "add_annotation_link_generator",
        "h.services.links.add_annotation_link_generator",
    )
    config.register_service_factory("h.services.links.links_factory", name="links")
    config.register_service_factory(
        "h.services.list_organizations.list_organizations_factory",
        name="list_organizations",
    )
    config.register_service_factory(
        "h.services.job_queue.metrics.factory", name="job_queue_metrics"
    )
    config.register_service_factory("h.services.nipsa.nipsa_factory", name="nipsa")
    config.register_service_factory(
        "h.services.oauth.service.factory", name="oauth_provider"
    )
    config.register_service_factory(
        "h.services.organization.organization_factory", name="organization"
    )
    config.register_service_factory(
        "h.services.search_index.factory", name="search_index"
    )
    config.register_service_factory(
        "h.services.settings.settings_factory", name="settings"
    )
    config.register_service_factory(
        "h.services.subscription.service_factory", iface=SubscriptionService
    )

    # User related services
    config.register_service_factory("h.services.user.user_service_factory", name="user")
    config.register_service_factory(
        "h.services.user_delete.service_factory", name="user_delete"
    )
    config.register_service_factory(
        "h.services.user_password.user_password_service_factory", name="user_password"
    )
    config.register_service_factory(
        "h.services.user_rename.service_factory", name="user_rename"
    )
    config.register_service_factory(
        "h.services.user_signup.user_signup_service_factory", name="user_signup"
    )
    config.register_service_factory(
        "h.services.user_unique.user_unique_factory", name="user_unique"
    )
    config.register_service_factory(
        "h.services.user_update.user_update_factory", name="user_update"
    )

    # Other services
    config.register_service_factory(
        "h.services.url_migration.service_factory", name="url_migration"
    )

"""The main h application."""

import logging
from urllib.parse import urlparse

import transaction
from pyramid.settings import asbool
from pyramid.tweens import EXCVIEW

from h.config import configure
from h.sentry_filters import SENTRY_FILTERS
from h.views.client import DEFAULT_CLIENT_URL

log = logging.getLogger(__name__)


def configure_jinja2_assets(config):
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.globals["asset_url"] = config.registry["assets_env"].url
    jinja2_env.globals["asset_urls"] = config.registry["assets_env"].urls


def in_debug_mode(request):
    return asbool(request.registry.settings.get("pyramid.debug_all"))


def create_app(global_config, **settings):
    """
    Create the h WSGI application.

    This function serves as a paste app factory.
    """
    config = configure(settings=settings)
    config.include(__name__)
    return config.make_wsgi_app()


def includeme(config):
    settings = config.registry.settings

    config.set_root_factory("h.traversal:Root")
    config.include("h.subscribers")

    config.add_tween("h.tweens.conditional_http_tween_factory", under=EXCVIEW)
    config.add_tween("h.tweens.rollback_db_session_on_exception_factory", under=EXCVIEW)
    config.add_tween("h.tweens.redirect_tween_factory")
    config.add_tween("h.tweens.invalid_path_tween_factory")
    config.add_tween("h.tweens.security_header_tween_factory")
    config.add_tween("h.tweens.cache_header_tween_factory")

    # While exclog is working it can access the database to add extra details
    # like the user id. If we happen after pyramid_tm the connection will have
    # already closed, we'll open another, and then get an unclosed handle.
    config.add_tween(
        "pyramid_exclog.exclog_tween_factory", under="pyramid_tm.tm_tween_factory"
    )

    config.add_request_method(in_debug_mode, "debug", reify=True)

    config.include("pyramid_jinja2")
    config.add_jinja2_extension("h.jinja_extensions.Filters")
    config.add_jinja2_extension("h.jinja_extensions.SvgIcon")
    # Register a deferred action to setup the assets environment
    # when the configuration is committed.
    config.action(None, configure_jinja2_assets, args=(config,))

    # Pyramid layouts: provides support for reusable components ('panels')
    # that are used across multiple pages
    config.include("pyramid_layout")

    config.registry.settings.setdefault(
        "mail.default_sender", '"Annotation Daemon" <no-reply@localhost>'
    )
    if asbool(config.registry.settings.get("h.debug")):
        config.include("pyramid_mailer.debug")
    else:
        config.include("pyramid_mailer")

    # Pyramid service layer: provides infrastructure for registering and
    # retrieving services bound to the request.
    config.include("pyramid_services")

    config.add_settings(
        {
            "tm.manager_hook": lambda request: transaction.TransactionManager(),
            "tm.annotate_user": False,
        }
    )
    config.include("pyramid_retry")
    config.include("pyramid_tm")

    # Add support for logging exceptions whenever they arise
    config.include("pyramid_exclog")
    config.add_settings({"exclog.extra_info": True})

    # Define the global default Content Security Policy
    client_url = settings.get("h.client_url", DEFAULT_CLIENT_URL)
    client_host = urlparse(client_url).netloc
    settings["csp"] = {
        "font-src": ["'self'", "fonts.gstatic.com", client_host],
        "script-src": ["'self'", client_host, "www.google-analytics.com"],
        # Allow inline styles until https://github.com/hypothesis/client/issues/293
        # is resolved as otherwise our own tool would break on the site,
        # including on /docs/help.
        "style-src": ["'self'", "fonts.googleapis.com", client_host, "'unsafe-inline'"],
    }
    if "csp.report_uri" in settings:
        settings["csp"]["report-uri"] = [settings["csp.report_uri"]]

    # Core site modules
    config.include("h.assets")
    config.include("h.auth")
    config.include("h.authz")
    config.include("h.db")
    config.include("h.eventqueue")
    config.include("h.form")
    config.include("h.indexer")
    config.include("h.panels")
    config.include("h.realtime")
    config.include("h.renderers")
    config.include("h.routes")
    config.include("h.search")
    config.include("h.services")
    config.include("h.session")
    config.include("h.viewderivers")
    config.include("h.viewpredicates")
    config.include("h.views")

    # Site modules
    config.include("h.accounts")
    config.include("h.links")
    config.include("h.nipsa")
    config.include("h.notification")

    # Configure sentry
    config.add_settings(
        {
            "h_pyramid_sentry.filters": SENTRY_FILTERS,
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.celery_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
        }
    )

    config.include("h_pyramid_sentry")

    # pyramid-sanity should be activated as late as possible
    config.include("pyramid_sanity")

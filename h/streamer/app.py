import os

import pyramid

from h.config import configure
from h.security import BearerTokenPolicy
from h.sentry_filters import SENTRY_FILTERS
from h.streamer.worker import log


def create_app(_global_config, **settings):
    config = configure(settings=settings)

    if os.environ.get("KILL_SWITCH_WEBSOCKET"):
        log.warning("Websocket kill switch has been enabled.")
        log.warning("The switch is the environment variable 'KILL_SWITCH_WEBSOCKET'")
        log.warning("No websocket functionality will work until the switch is disabled")

        # Add views to return messages so we don't get confused between
        # disabled and missing end-points in the logs
        config.scan("h.streamer.kill_switch_views")

        # Quit out early without configuring any routes etc.
        return config.make_wsgi_app()

    config.include("pyramid_services")

    config.include("h.security")
    # Override the default authentication policy.
    config.set_security_policy(BearerTokenPolicy())

    config.include("h.db")
    config.include("h.session")
    config.include("h.services")

    # We include links in order to set up the alternative link registrations
    # for annotations.
    config.include("h.links")

    # And finally we add routes. Static routes are not resolvable by HTTP
    # clients, but can be used for URL generation within the websocket server.
    config.add_route("ws", "/ws")
    config.add_route("annotation", "/a/{id}", static=True)
    config.add_route("api.annotation", "/api/annotations/{id}", static=True)

    # Health check
    config.scan("h.views.status")
    config.add_route("status", "/_status")

    config.scan("h.streamer.views")
    config.scan("h.streamer.streamer")
    config.add_tween(
        "h.streamer.tweens.close_db_session_tween_factory",
        over=["pyramid_exclog.exclog_tween_factory", pyramid.tweens.EXCVIEW],
    )

    # Configure sentry
    config.add_settings(
        {
            "h_pyramid_sentry.filters": SENTRY_FILTERS,
            "h_pyramid_sentry.celery_support": True,
        }
    )

    config.include("h_pyramid_sentry")

    # Add support for logging exceptions whenever they arise
    config.include("pyramid_exclog")
    config.add_settings({"exclog.extra_info": True})

    return config.make_wsgi_app()

import pyramid

from h._version import get_version
from h.config import configure
from h.security import StreamerPolicy
from h.sentry_filters import SENTRY_ERROR_FILTERS


def create_app(_global_config, **settings):
    config = configure(settings=settings)

    config.include("pyramid_services")

    config.include("h.security")
    # Override the default authentication policy.
    config.set_security_policy(StreamerPolicy())

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
    config.add_route("activity.user_search", "/users/{username}", static=True)

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
            "h_pyramid_sentry.filters": SENTRY_ERROR_FILTERS,
            "h_pyramid_sentry.celery_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
            # Enable Sentry's "Releases" feature, see:
            # https://docs.sentry.io/platforms/python/configuration/options/#release
            #
            # h_pyramid_sentry passes any h_pyramid_sentry.init.* Pyramid settings
            # through to sentry_sdk.init(), see:
            # https://github.com/hypothesis/h-pyramid-sentry?tab=readme-ov-file#settings
            #
            # For the full list of options that sentry_sdk.init() supports see:
            # https://docs.sentry.io/platforms/python/configuration/options/
            "h_pyramid_sentry.init.release": get_version(),
        }
    )

    config.include("h_pyramid_sentry")

    # Add support for logging exceptions whenever they arise
    config.include("pyramid_exclog")
    config.add_settings({"exclog.extra_info": True})

    return config.make_wsgi_app()

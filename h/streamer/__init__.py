from h.streamer.tweens import close_db_session_tween_factory

__all__ = ["close_db_session_tween_factory"]


def includeme(config):  # pragma: no cover
    config.include("h.streamer.views")
    config.include("h.streamer.metrics")

    config.add_subscriber(
        "h.streamer.streamer.start", "pyramid.events.ApplicationCreated"
    )

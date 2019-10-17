from h.streamer.tweens import close_db_session_tween_factory

__all__ = ["close_db_session_tween_factory"]


def includeme(config):
    config.include("h.streamer.views")

    config.add_subscriber(
        "h.streamer.streamer.start", "pyramid.events.ApplicationCreated"
    )

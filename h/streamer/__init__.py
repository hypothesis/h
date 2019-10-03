# -*- coding: utf-8 -*-


def includeme(config):
    config.include("h.streamer.views")

    config.add_subscriber(
        "h.streamer.streamer.start", "pyramid.events.ApplicationCreated"
    )

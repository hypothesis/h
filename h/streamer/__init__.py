# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def includeme(config):
    config.include("h.streamer.views")

    config.add_subscriber(
        "h.streamer.streamer.start", "pyramid.events.ApplicationCreated"
    )

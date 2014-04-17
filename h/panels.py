# -*- coding: utf-8 -*-
from pyramid_layout.panel import panel_config


def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)

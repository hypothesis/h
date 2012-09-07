import colander
import horus

from pyramid_layout.layout import layout_config


def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)

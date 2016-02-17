# -*- coding: utf-8 -*-

from pyramid.view import view_config


def json_view(**settings):
    """A view configuration decorator with JSON defaults."""
    settings.setdefault('accept', 'application/json')
    settings.setdefault('renderer', 'json')
    return view_config(**settings)

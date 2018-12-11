# -*- coding: utf-8 -*-

"""Help and documentation views."""

from __future__ import unicode_literals

import binascii
import os

from pyramid import httpexceptions as exc
from pyramid.view import view_config


@view_config(renderer="h:templates/help.html.jinja2", route_name="custom_onboarding")
def custom_onboarding_page(context, request):
    return {
        "embed_js_url": request.route_path("embed"),
        "is_help": False,
        "is_onboarding": True,
    }


@view_config(renderer="h:templates/help.html.jinja2", route_name="onboarding")
def onboarding_page(context, request):
    return exc.HTTPFound(request.route_url("custom_onboarding", slug=_random_word()))


@view_config(renderer="h:templates/help.html.jinja2", route_name="help")
def help_page(context, request):
    return {
        "embed_js_url": request.route_path("embed"),
        "is_help": True,
        "is_onboarding": False,
    }


def _random_word():
    return binascii.hexlify(os.urandom(8))

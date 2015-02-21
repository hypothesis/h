# -*- coding: utf-8 -*-
from pyramid_layout.layout import layout_config

from h.layouts import BaseLayout


@layout_config(name='auth', template='h:templates/layouts/base.html')
class AuthLayout(BaseLayout):
    app = 'h'
    controller = 'AuthAppController'
    requirements = (('app', None), ('account', None))


def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)

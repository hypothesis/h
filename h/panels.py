# -*- coding: utf-8 -*-
def includeme(config):
    config.include('pyramid_layout')
    config.scan(__name__)

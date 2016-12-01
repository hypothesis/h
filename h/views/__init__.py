# -*- coding: utf-8 -*-


def includeme(config):
    config.scan(__name__)
    config.include('h.views.predicates')

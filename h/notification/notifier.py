# -*- coding: utf-8 -*-
class TemplateRenderException(Exception):
    pass


def includeme(config):
    config.scan(__name__)

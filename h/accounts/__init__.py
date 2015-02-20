# -*- coding: utf-8 -*-
def includeme(config):
    """A local identity provider."""
    config.include('.layouts')
    config.include('.models')
    config.include('.schemas')
    config.include('.subscribers')
    config.include('.views')

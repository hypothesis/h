# -*- coding: utf-8 -*-
def includeme(config):
    config.include('.types')
    config.include('.gateway')
    config.include('.models')
    config.include('.notifier')
    config.include('.reply_template')

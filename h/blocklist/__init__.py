# -*- coding: utf-8 -*-
from h.blocklist.models import Blocklist


def includeme(config):
    config.include('.views')

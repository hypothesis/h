# -*- coding: utf-8 -*-
from h.groups.logic import as_dict


__all__ = ('as_dict',)


def includeme(config):
    config.include('.views')

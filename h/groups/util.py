# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models


def fetch_group(request, id_):
    return request.db.query(models.Group).filter_by(pubid=id_).one_or_none()

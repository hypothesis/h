# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import models

from .base import ModelFactory


class FeatureCohort(ModelFactory):

    class Meta:
        model = models.FeatureCohort

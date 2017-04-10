# -*- coding: utf-8 -*-

from h import models

from .base import ModelFactory


class Activation(ModelFactory):

    class Meta:
        model = models.Activation
        force_flush = True

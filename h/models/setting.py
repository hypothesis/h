# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from h.db import Base
from h.db import mixins


class Setting(Base, mixins.Timestamps):

    """A setting set by the application and shared with other processes."""

    __tablename__ = "setting"

    #: The setting key
    key = sa.Column(sa.UnicodeText(), primary_key=True)

    #: The setting value
    value = sa.Column(sa.UnicodeText())

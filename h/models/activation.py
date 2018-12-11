# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import hashlib
import random
import string

import sqlalchemy as sa

from h._compat import text_type
from h.db import Base


def _generate_random_string(length=12):
    """Generate a random ascii string of the requested length."""
    msg = hashlib.sha256()
    word = ""
    for _ in range(length):
        word += random.choice(string.ascii_letters)
    msg.update(word.encode("ascii"))
    return text_type(msg.hexdigest()[:length])


class Activation(Base):

    """
    Handles activations for users.

    The code should be a random hash that is valid only once.
    After the hash is used to access the site, it'll be removed.
    """

    __tablename__ = "activation"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # A random hash that is valid only once.
    code = sa.Column(
        sa.UnicodeText(), nullable=False, unique=True, default=_generate_random_string
    )

    @classmethod
    def get_by_code(cls, session, code):
        """Fetch an activation by code."""
        return session.query(cls).filter(cls.code == code).first()

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Generate random strings for use as identifiers in URLs (and other places).

The random strings are generated using an alphabet of ASCII digits and letters
with the following removed:

  - 0, O, I, 1: easily mistaken for one another when reading a URL.
  - C, c, F, f, H, h, S, s, U, u, T, t: avoid making curse words accidentally.

With a default length of n characters, the size of the space of possible
strings is:

    N = len(ALPHABET) ** n

The chance of a collision when generating k random ids of length n is
approximately:

   k**2
   ----
    2N

(for sufficiently large k and N). This means that with a default length of 8,
as here, we have a 99.97% chance of generating 100,000 strings in a row without
collisions, so we hopefully won't need to worry about that any time soon.

Reference: http://preshing.com/20110504/hash-collision-probabilities/
"""

import random

ALPHABET = "123456789ABDEGJKLMNPQRVWXYZabdegijkmnopqrvwxyz"
DEFAULT_LENGTH = 8


def generate(length=DEFAULT_LENGTH):
    """
    Generate a random string of the specified length.

    The returned string is composed of an alphabet that shouldn't include any
    characters that are easily mistakeable for one another (I, 1, O, 0), and
    hopefully won't accidentally contain any English-language curse words.
    """
    return "".join(random.SystemRandom().choice(ALPHABET) for _ in range(length))

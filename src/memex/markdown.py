# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

import mistune

# Singleton instance of the Markdown instance
markdown = None


def render(text):
    if text is not None:
        render = _get_markdown()
        return render(text)
    return None


def _get_markdown():
    global markdown
    if markdown is None:
        markdown = mistune.Markdown(escape=True)
    return markdown

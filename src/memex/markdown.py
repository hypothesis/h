# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

import bleach
from bleach import callbacks as linkify_callbacks
import mistune

MARKDOWN_TAGS = [
    'a', 'blockquote', 'code', 'em', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'img', 'li', 'ol', 'p', 'pre', 'strong', 'ul',
]
ALLOWED_TAGS = set(bleach.ALLOWED_TAGS + MARKDOWN_TAGS)


def _filter_link_attributes(name, value):
    if name in ['href', 'title']:
        return True

    if name == 'target' and value == '_blank':
        return True

    return False

MARKDOWN_ATTRIBUTES = {
    'a': _filter_link_attributes,
    'img': ['alt', 'src', 'title'],
}
ALLOWED_ATTRIBUTES = dict(bleach.ALLOWED_ATTRIBUTES.items() + MARKDOWN_ATTRIBUTES.items())

# Singleton instance of the Markdown instance
markdown = None


class MathMarkdown(mistune.Markdown):
    def output_block_math(self):
        return self.renderer.block_math(self.token['text'])


class MathInlineLexer(mistune.InlineLexer):
    def __init__(self, *args, **kwargs):
        super(MathInlineLexer, self).__init__(*args, **kwargs)
        self.rules.inline_math = re.compile(r'\\\((.*?)\\\)', re.DOTALL)
        self.default_rules.insert(0, 'inline_math')

    def output_inline_math(self, m):
        return self.renderer.inline_math(m.group(1))


class MathBlockLexer(mistune.BlockLexer):
    def __init__(self, *args, **kwargs):
        super(MathBlockLexer, self).__init__(*args, **kwargs)
        self.rules.block_math = re.compile(r'^\$\$(.*?)\$\$', re.DOTALL)
        self.default_rules.insert(0, 'block_math')

    def parse_block_math(self, m):
        self.tokens.append({
            'type': 'block_math',
            'text': m.group(1)
        })


class MathRenderer(mistune.Renderer):
    def __init__(self, **kwargs):
        super(MathRenderer, self).__init__(**kwargs)

    def block_math(self, text):
        return '<p>$$%s$$</p>\n' % text

    def inline_math(self, text):
        return '\\(%s\\)' % text


def render(text):
    if text is not None:
        render = _get_markdown()
        return sanitize(render(text))
    return None


def sanitize(text):
    linkified = bleach.linkify(text, callbacks=[
        linkify_callbacks.target_blank
    ])

    return bleach.clean(linkified,
                        tags=ALLOWED_TAGS,
                        attributes=ALLOWED_ATTRIBUTES)


def _get_markdown():
    global markdown
    if markdown is None:
        markdown = MathMarkdown(renderer=MathRenderer(),
                                inline=MathInlineLexer,
                                block=MathBlockLexer,
                                escape=True)
    return markdown

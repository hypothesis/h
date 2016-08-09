# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

import mistune

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
        return render(text)
    return None


def _get_markdown():
    global markdown
    if markdown is None:
        markdown = MathMarkdown(renderer=MathRenderer(),
                                inline=MathInlineLexer,
                                block=MathBlockLexer,
                                escape=True)
    return markdown

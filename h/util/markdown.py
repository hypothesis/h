# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from functools import partial

import bleach
import mistune
from bleach.linkifier import LinkifyFilter

LINK_REL = "nofollow noopener"

MARKDOWN_TAGS = [
    "a",
    "blockquote",
    "code",
    "em",
    "hr",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
]
ALLOWED_TAGS = set(bleach.ALLOWED_TAGS + MARKDOWN_TAGS)


def _filter_link_attributes(tag, name, value):
    if name in ["href", "title"]:
        return True

    if name == "target" and value == "_blank":
        return True

    if name == "rel" and value == LINK_REL:
        return True

    return False


MARKDOWN_ATTRIBUTES = {"a": _filter_link_attributes, "img": ["alt", "src", "title"]}

ALLOWED_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES.copy()
ALLOWED_ATTRIBUTES.update(MARKDOWN_ATTRIBUTES)

# Singleton instance of the bleach cleaner
cleaner = None
# Singleton instance of the Markdown instance
markdown = None


class MathMarkdown(mistune.Markdown):
    def output_block_math(self):
        return self.renderer.block_math(self.token["text"])


class MathInlineLexer(mistune.InlineLexer):
    def __init__(self, *args, **kwargs):
        super(MathInlineLexer, self).__init__(*args, **kwargs)
        self.rules.inline_math = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
        self.default_rules.insert(0, "inline_math")

    def output_inline_math(self, m):
        return self.renderer.inline_math(m.group(1))


class MathBlockLexer(mistune.BlockLexer):
    def __init__(self, *args, **kwargs):
        super(MathBlockLexer, self).__init__(*args, **kwargs)
        self.rules.block_math = re.compile(r"^\$\$(.*?)\$\$", re.DOTALL)
        self.default_rules.insert(0, "block_math")

    def parse_block_math(self, m):
        self.tokens.append({"type": "block_math", "text": m.group(1)})


class MathRenderer(mistune.Renderer):
    def __init__(self, **kwargs):
        super(MathRenderer, self).__init__(**kwargs)

    def block_math(self, text):
        return "<p>$$%s$$</p>\n" % text

    def inline_math(self, text):
        return "\\(%s\\)" % text


def render(text):
    if text is not None:
        render = _get_markdown()
        return sanitize(render(text))
    return None


def sanitize(text):
    cleaner = _get_cleaner()
    return cleaner.clean(text)


def _linkify_target_blank(attrs, new=False):
    # FIXME: when bleach>2.0.0 is released we can use
    # bleach.callbacks.target_blank instead of this function. We have our own
    # copy to work around a bug in 2.0.0:
    #
    #   https://github.com/mozilla/bleach/commit/b23c74c1ca5ffcbd308df93e79487fa92a6eb4a7
    #
    href_key = (None, "href")

    if href_key not in attrs:
        return attrs

    if attrs[href_key].startswith("mailto:"):
        return attrs

    attrs[(None, "target")] = "_blank"
    return attrs


def _linkify_rel(attrs, new=False):
    href_key = (None, "href")

    if href_key not in attrs:
        return attrs

    if attrs[href_key].startswith("mailto:"):
        return attrs

    attrs[(None, "rel")] = LINK_REL
    return attrs


def _get_cleaner():
    global cleaner
    if cleaner is None:
        linkify_filter = partial(
            LinkifyFilter, callbacks=[_linkify_target_blank, _linkify_rel]
        )
        cleaner = bleach.Cleaner(
            tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, filters=[linkify_filter]
        )
    return cleaner


def _get_markdown():
    global markdown
    if markdown is None:
        markdown = MathMarkdown(
            renderer=MathRenderer(),
            inline=MathInlineLexer,
            block=MathBlockLexer,
            escape=True,
        )
    return markdown

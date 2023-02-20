from functools import lru_cache, partial

import bleach
from bleach.linkifier import LinkifyFilter
from markdown import Markdown

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

RENDER_MARKDOWN = Markdown().convert


def render(text):
    """
    Render Markdown text and remove dangerous HTML.

    HTML which is provided by Markdown and some extensions are allowed.

    :param text: Markdown format text to be rendered
    :return: HTML text
    """
    if text is None:
        return None

    # We use a non-standard math extension to Markdown which is delimited
    # by either `$$` or `\( some maths \)`. The escaped brackets are
    # naturally converted into literal brackets in Markdown, so to preserve
    # them we'll double escape them.
    text = text.replace("\\(", "\\\\(").replace("\\)", "\\\\)")

    return _get_cleaner().clean((RENDER_MARKDOWN(text)))


def _filter_link_attributes(_tag, name, value):
    if name in ["href", "title"]:
        return True

    if name == "target" and value == "_blank":
        return True

    if name == "rel" and value == LINK_REL:
        return True

    return False


def _linkify_target_blank(attrs, new=False):  # pylint: disable=unused-argument
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


def _linkify_rel(attrs, new=False):  # pylint: disable=unused-argument
    href_key = (None, "href")

    if href_key not in attrs:
        return attrs

    if attrs[href_key].startswith("mailto:"):
        return attrs

    attrs[(None, "rel")] = LINK_REL
    return attrs


ALLOWED_TAGS = set(bleach.ALLOWED_TAGS) | set(MARKDOWN_TAGS)

MARKDOWN_ATTRIBUTES = {"a": _filter_link_attributes, "img": ["alt", "src", "title"]}
ALLOWED_ATTRIBUTES = bleach.ALLOWED_ATTRIBUTES.copy()
ALLOWED_ATTRIBUTES.update(MARKDOWN_ATTRIBUTES)


@lru_cache(maxsize=None)
def _get_cleaner():
    linkify_filter = partial(
        LinkifyFilter, callbacks=[_linkify_target_blank, _linkify_rel]
    )
    cleaner = bleach.Cleaner(
        tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, filters=[linkify_filter]
    )
    return cleaner

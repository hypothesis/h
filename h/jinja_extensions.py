# -*- coding: utf-8 -*-

import datetime
from functools import partial
import json

try:
    from xml.etree import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

from jinja2 import Markup
from jinja2.ext import Extension

SVG_NAMESPACE_URI = 'http://www.w3.org/2000/svg'


class Filters(Extension):

    """
    Set up filters for Jinja2.
    """

    def __init__(self, environment):
        super(Filters, self).__init__(environment)

        environment.filters['to_json'] = to_json
        environment.filters['human_timestamp'] = human_timestamp


def human_timestamp(timestamp, now=datetime.datetime.utcnow):
    """Turn a :py:class:`datetime.datetime` into a human-friendly string."""
    fmt = '%d %B at %H:%M'
    if timestamp.year < now().year:
        fmt = '%d %B %Y at %H:%M'
    return timestamp.strftime(fmt)


def to_json(value):
    """
    Serialize a value as an HTML-safe JSON string.

    The resulting value can be safely used inside a <script> tag in an HTML
    document.

    See http://benalpert.com/2012/08/03/preventing-xss-json.html for an
    explanation of why JSON needs to be escaped when embedding it in an HTML
    context.
    """

    # Adapted from Flask's htmlsafe_dumps() function / tojson filter.
    result = json.dumps(value) \
                 .replace(u'<', u'\\u003c') \
                 .replace(u'>', u'\\u003e') \
                 .replace(u'&', u'\\u0026') \
                 .replace(u"'", u'\\u0027')

    return Markup(result)


class SvgIcon(Extension):

    """
    Setup helpers for rendering icons.
    """

    def __init__(self, environment):
        super(SvgIcon, self).__init__(environment)

        def read_icon(name):
            return open('build/images/icons/{}.svg'.format(name)).read()

        environment.globals['svg_icon'] = partial(svg_icon, read_icon)


def svg_icon(loader, name, css_class=''):
    """
    Return inline SVG markup for an icon.

    This is a helper for generating inline SVGs for rendering icons in HTML
    that can be customized via CSS.
    See https://github.com/blog/2112-delivering-octicons-with-svg

    To color an icon dynamically (eg. on hover), apply a CSS class to the SVG
    via the `css_class` property, style the `color` property for the relevant
    pseudo-class (eg. `:hover`) and use `fill="currentColor"` or
    `stroke="currentColor"` in the SVG markup.

    :param loader: Callable accepting an icon name and returning XML markup for
                   the SVG.
    :param name: The name of the SVG file to render
    :param css_class: CSS class attribute for the returned `<svg>` element. The
                      'svg-icon' class will be added in addition to any classes
                      specified here.
    """

    # Register SVG as the default namespace. This avoids a problem where
    # ElementTree otherwise serializes SVG elements with an 'ns0' namespace (eg.
    # '<ns0:svg>...') and browsers will not render the result as SVG.
    # See http://stackoverflow.com/questions/8983041
    ElementTree.register_namespace('', SVG_NAMESPACE_URI)
    root = ElementTree.fromstring(loader(name))

    if css_class:
        css_class = 'svg-icon ' + css_class
    else:
        css_class = 'svg-icon'
    root.set('class', css_class)

    # If the SVG has its own title, ignore it in favor of the title attribute
    # of the <svg> or its containing element, which is usually a link.
    title_el = root.find('{{{}}}title'.format(SVG_NAMESPACE_URI))
    if title_el is not None:
        root.remove(title_el)

    return Markup(ElementTree.tostring(root))

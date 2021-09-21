from xml.etree import ElementTree

from markupsafe import Markup

SVG_NAMESPACE_URI = "http://www.w3.org/2000/svg"


def svg_icon(name, css_class=""):
    """
    Return inline SVG markup for an icon.

    This is a helper for generating inline SVGs for rendering icons in HTML
    that can be customized via CSS.
    See https://github.com/blog/2112-delivering-octicons-with-svg

    To color an icon dynamically (eg. on hover), apply a CSS class to the SVG
    via the `css_class` property, style the `color` property for the relevant
    pseudo-class (eg. `:hover`) and use `fill="currentColor"` or
    `stroke="currentColor"` in the SVG markup.

    :param name: The name of the SVG file to render
    :param css_class: CSS class attribute for the returned `<svg>` element. The
        'svg-icon' class will be added in addition to any classes specified
        here.
    """

    # Register SVG as the default namespace. This avoids a problem where
    # ElementTree otherwise serializes SVG elements with an 'ns0' namespace (eg.
    # '<ns0:svg>...') and browsers will not render the result as SVG.
    # See http://stackoverflow.com/questions/8983041
    ElementTree.register_namespace("", SVG_NAMESPACE_URI)

    with open(f"build/images/icons/{name}.svg", encoding="utf8") as handle:
        svg_data = handle.read()

    root = ElementTree.fromstring(svg_data)

    if css_class:
        css_class = "svg-icon " + css_class
    else:
        css_class = "svg-icon"

    root.set("class", css_class)

    # If the SVG has its own title, ignore it in favor of the title attribute
    # of the <svg> or its containing element, which is usually a link.
    title_el = root.find(f"{{{SVG_NAMESPACE_URI}}}title")
    if title_el is not None:
        root.remove(title_el)

    return Markup(ElementTree.tostring(root).decode())

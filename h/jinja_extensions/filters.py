import datetime
import json

from markupsafe import Markup


def human_timestamp(timestamp, now=datetime.datetime.utcnow):
    """Turn a :py:class:`datetime.datetime` into a human-friendly string."""
    fmt = "%d %B at %H:%M"
    if timestamp.year < now().year:
        fmt = "%d %B %Y at %H:%M"
    return timestamp.strftime(fmt)


def format_number(num):
    return f"{num:,}"


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
    result = (
        json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("'", "\\u0027")
    )

    return Markup(result)

from urllib.parse import unquote

from h.jinja_extensions import filters
from h.jinja_extensions.svg_icon import svg_icon


def setup_jinja2_env(environment):
    # 3rd party filters
    environment.filters["url_unquote"] = unquote

    # 1st party filters
    environment.filters["to_json"] = filters.to_json
    environment.filters["human_timestamp"] = filters.human_timestamp
    environment.filters["format_number"] = filters.format_number

    # 1st party globals
    environment.globals["svg_icon"] = svg_icon


def includeme(config):  # pragma: no cover
    # See: https://docs.pylonsproject.org/projects/pyramid_jinja2/en/latest/api.html#pyramid_jinja2.get_jinja2_environment
    config.action(
        None, lambda: setup_jinja2_env(config.get_jinja2_environment()), order=999
    )

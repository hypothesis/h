from urllib.parse import unquote

from h.jinja_extensions import filters
from h.jinja_extensions.back_link_label import back_link_label
from h.jinja_extensions.navbar_data import navbar_data
from h.jinja_extensions.navbar_data_admin import navbar_data_admin
from h.jinja_extensions.svg_icon import svg_icon


def setup_jinja2_env(environment):
    # Filters written by someone else (not hypothesis)
    environment.filters["url_unquote"] = unquote

    # Filters written by us
    environment.filters["to_json"] = filters.to_json
    environment.filters["human_timestamp"] = filters.human_timestamp
    environment.filters["format_number"] = filters.format_number

    # Globals provided by us
    environment.globals["svg_icon"] = svg_icon
    environment.globals["back_link_label"] = back_link_label
    environment.globals["navbar_data"] = navbar_data
    environment.globals["navbar_data_admin"] = navbar_data_admin


def includeme(config):  # pragma: no cover
    # See: https://docs.pylonsproject.org/projects/pyramid_jinja2/en/latest/api.html#pyramid_jinja2.get_jinja2_environment
    config.action(
        None, lambda: setup_jinja2_env(config.get_jinja2_environment()), order=999
    )

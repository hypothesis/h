from urllib.parse import unquote

from h_matchers import Any
from jinja2 import Environment

from h.jinja_extensions import filters, setup_jinja2_env
from h.jinja_extensions.back_link_label import back_link_label
from h.jinja_extensions.navbar_data import navbar_data
from h.jinja_extensions.svg_icon import svg_icon


class TestSetupJinja2Env:
    def test_it(self):
        environment = Environment()

        setup_jinja2_env(environment)

        assert environment.filters == Any.dict.containing(
            {
                "to_json": filters.to_json,
                "human_timestamp": filters.human_timestamp,
                "format_number": filters.format_number,
                "url_unquote": unquote,
            }
        )

        assert environment.globals == Any.dict.containing(
            {
                "svg_icon": svg_icon,
                "back_link_label": back_link_label,
                "navbar_data": navbar_data,
            }
        )

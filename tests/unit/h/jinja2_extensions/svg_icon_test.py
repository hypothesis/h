import os

import pytest
from markupsafe import Markup

from h.jinja_extensions import svg_icon


class TestSVGIcon:
    def test_it_removes_title(self, icon_file):
        icon_file.write(
            '<svg xmlns="http://www.w3.org/2000/svg"><title>foo</title></svg>'
        )

        assert svg_icon("test_icon_name") == Markup(
            '<svg xmlns="http://www.w3.org/2000/svg" class="svg-icon" />'
        )

    def test_it_strips_default_xml_namespace(self, icon_file):
        icon_file.write('<svg xmlns="http://www.w3.org/2000/svg"></svg>')

        assert svg_icon("test_icon_name") == Markup(
            '<svg xmlns="http://www.w3.org/2000/svg" class="svg-icon" />'
        )

    @pytest.mark.parametrize(
        "css_class,expected",
        ((None, "svg-icon"), ("fancy-icon", "svg-icon fancy-icon")),
    )
    def test_it_sets_css_class(self, icon_file, css_class, expected):
        icon_file.write("<svg></svg>")

        result = svg_icon("test_icon_name", css_class=css_class)

        assert result == Markup(f'<svg class="{expected}" />')

    @pytest.fixture
    def icon_file(self, tmpdir):
        os.chdir(tmpdir)

        icon_dir = tmpdir / "build" / "images" / "icons"
        icon_dir.ensure_dir()

        return icon_dir / "test_icon_name.svg"

import pytest
from importlib_resources import files

from h.sql_tasks.sql_query import SQLQuery
from h.sql_tasks.sql_script import SQLScript


class TestSQLScript:
    def test_from_dir(self):
        fixture_dir = files("tests.h.sql_tasks") / "script_fixture"

        template_vars = {"template_var": "template_value"}

        scripts = list(
            SQLScript.from_dir(task_dir=str(fixture_dir), template_vars=template_vars)
        )

        assert scripts == [
            SQLScript(
                path=str(fixture_dir / "01_file.sql"),
                template_vars=template_vars,
                queries=[
                    SQLQuery(index=0, text="-- Comment 1\nSELECT 1;"),
                    SQLQuery(index=1, text="-- Comment 2\nSELECT 2;"),
                ],
            ),
            SQLScript(
                path=str(fixture_dir / "02_dir/01_file.sql"),
                template_vars=template_vars,
                queries=[SQLQuery(index=0, text="SELECT 3")],
            ),
            SQLScript(
                path=str(fixture_dir / "03_file.jinja2.sql"),
                template_vars=template_vars,
                queries=[SQLQuery(index=0, text="SELECT 'template_value';")],
            ),
        ]

    def test_from_dir_raises_for_missing_dir(self):
        with pytest.raises(NotADirectoryError):
            list(SQLScript.from_dir("/i_do_not_exist", {}))

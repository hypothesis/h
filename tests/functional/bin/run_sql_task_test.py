import os
from subprocess import check_output

from importlib_resources import files
from pytest import fixture


class TestRunSQLTask:
    def test_it(self, environ):
        result = check_output(
            [
                "python",
                "bin/run_sql_task.py",
                "--config-file",
                "conf/development-app.ini",
                "--task",
                "hello_world",
            ],
            env=environ,
        )

        assert result

    @fixture
    def environ(self):
        environ = dict(os.environ)
        environ["PYTHONPATH"] = "."

        return environ

    @fixture(autouse=True)
    def run_in_root(self):
        # A context manager to ensure we work from the root, but return the
        # path to where it was before
        current_dir = os.getcwd()
        os.chdir(str(files("h") / ".."))

        yield

        os.chdir(current_dir)

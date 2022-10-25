import os
import os.path
from dataclasses import dataclass
from typing import List

import jinja2
import sqlparse

from h.sql_tasks.sql_query import SQLQuery


@dataclass
class SQLScript:
    """A class representing an SQL file with multiple queries."""

    path: str
    """Full path of the script."""

    template_vars: dict
    """Template vars to pass to templated SQL statements."""

    queries: List[SQLQuery] = None
    """Queries contained in this file."""

    _jinja_env = jinja2.Environment(undefined=jinja2.StrictUndefined)

    def __post_init__(self):
        if not self.queries:
            self.queries = self._parse()

    @classmethod
    def from_dir(cls, task_dir: str, template_vars: dict):
        """
        Generate `SQLFile` objects from files found in a directory.

        This will return a generator of `SQLFile` based on the natural sorting
        order of files found in the directory, and subdirectories. Only files
        with a `.sql` prefix are considered. Files with `.jinja2.sql` are
        treated as Jinja2 templated SQL and are rendered using the provided
        environment.

        :param task_dir: The directory to read from
        :param template_vars: Variables to include in Jinja2 SQL files
        """
        if not os.path.isdir(task_dir):
            raise NotADirectoryError(f"Cannot find the task directory: '{task_dir}'")

        for item in sorted(os.listdir(task_dir)):
            full_name = os.path.join(task_dir, item)

            if os.path.isdir(full_name):
                yield from cls.from_dir(full_name, template_vars=template_vars)

            elif full_name.endswith(".sql"):
                yield SQLScript(full_name, template_vars=template_vars)

    def _parse(self):
        with open(self.path, encoding="utf-8") as handle:
            script_text = handle.read()

        if self.path.endswith("jinja2.sql"):
            # Looks like this file has been templated
            script_text = self._jinja_env.from_string(script_text).render(
                self.template_vars
            )

        return [
            SQLQuery(text=query, index=index)
            for index, query in (enumerate(sqlparse.split(script_text)))
        ]

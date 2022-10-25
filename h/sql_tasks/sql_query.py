import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.engine import Connection
from tabulate import tabulate


@dataclass
class SQLQuery:
    """A class representing an individual SQL query."""

    index: int
    """Index of this query inside the script."""

    text: str
    """Text of the query."""

    start_time: datetime = None
    """Time execution began."""

    duration: timedelta = None
    """Duration of query execution."""

    columns: Optional[list] = None
    """Columns of the returned values (if any)."""

    rows: Optional[list] = None
    """Rows of the returned values (if any)."""

    def execute(self, connection: Connection):
        """Execute this query in the given session."""

        self.start_time = datetime.now()

        cursor = connection.execute(sa.text(self.text))
        if cursor.returns_rows:
            self.columns = [col.name for col in cursor.cursor.description]
            self.rows = cursor.fetchall()

        self.duration = datetime.now() - self.start_time

    def dump(self, indent=""):
        """
        Get a string representation of this query like psql's format.

        :param indent: Optional indenting string prepended to each line.
        """

        text = textwrap.indent(self.text, prefix=f"{self.index}=> ")
        if self.rows:
            text += "\n" + tabulate(
                tabular_data=[list(row) for row in self.rows],
                headers=self.columns,
                tablefmt="psql",
            )
        text += f"\n\nTime: {self.duration}"
        return textwrap.indent(text, indent)

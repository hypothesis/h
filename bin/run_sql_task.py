"""
Task runner for tasks written as SQL files in directories.

This is a general mechanism for running tasks defined in SQL, however it's
currently only used to perform the aggregations and mappings required for
reporting.
"""
from argparse import ArgumentParser

import importlib_resources
from psycopg2.extensions import parse_dsn
from pyramid.paster import bootstrap

from h.sql_tasks.sql_script import SQLScript

TASK_ROOT = importlib_resources.files("h.sql_tasks") / "tasks"

parser = ArgumentParser(
    description=f"A script for running SQL tasks defined in: {TASK_ROOT}"
)
parser.add_argument(
    "-c",
    "--config-file",
    required=True,
    help="The paster config for this application. (e.g. development.ini)",
)

parser.add_argument("-t", "--task", required=True, help="The SQL task name to run")


def main():
    args = parser.parse_args()

    with bootstrap(args.config_file) as env:
        request = env["request"]
        dsn = env["registry"].settings["sqlalchemy.url"].strip()

        scripts = SQLScript.from_dir(
            task_dir=TASK_ROOT / args.task,
            template_vars={"db_user": parse_dsn(dsn)["user"]},
        )

        # Run the update in a transaction, so we roll back if it goes wrong
        with request.tm:
            with request.db.bind.connect() as connection:
                for script in scripts:
                    print(f"Executing: {script.path}")

                    for query in script.queries:
                        query.execute(connection)
                        print(query.dump(indent="    ") + "\n")


if __name__ == "__main__":
    main()

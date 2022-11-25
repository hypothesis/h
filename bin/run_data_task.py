"""
Task runner for tasks written as SQL files in directories.

This is a general mechanism for running tasks defined in SQL, however it's
currently only used to perform the aggregations and mappings required for
reporting.
"""
from argparse import ArgumentParser

import data_tasks
import importlib_resources
from data_tasks.python_script import PythonScript
from psycopg2.extensions import parse_dsn
from pyramid.paster import bootstrap

TASK_ROOT = importlib_resources.files("h.data_tasks")

parser = ArgumentParser(
    description=f"A script for running tasks defined in: {TASK_ROOT}"
)
parser.add_argument(
    "-c",
    "--config-file",
    required=True,
    help="The paster config for this application. (e.g. development.ini)",
)

parser.add_argument("-t", "--task", required=True, help="The task name to run")

parser.add_argument(
    "--no-python",
    action="store_const",
    default=False,
    const=True,
    help="Skip Python executables",
)
parser.add_argument(
    "--dry-run",
    action="store_const",
    default=False,
    const=True,
    help="Run through the task without executing anything for real",
)


def main():
    args = parser.parse_args()

    with bootstrap(args.config_file) as env:
        request = env["request"]
        dsn = env["registry"].settings["sqlalchemy.url"].strip()

        scripts = data_tasks.from_dir(
            task_dir=TASK_ROOT / args.task,
            template_vars={
                "db_user": parse_dsn(dsn)["user"],
                "fdw_users": env["registry"].settings.get("h.report.fdw_users", []),
            },
        )

        # Run the update in a transaction, so we roll back if it goes wrong
        with request.db.bind.connect() as connection:
            with connection.begin():
                for script in scripts:
                    if args.no_python and isinstance(script, PythonScript):
                        print(f"Skipping: {script}")
                        continue

                    for step in script.execute(connection, dry_run=args.dry_run):
                        if args.dry_run:
                            print("Dry run!")

                        print(step.dump(indent="    ") + "\n")


if __name__ == "__main__":
    main()

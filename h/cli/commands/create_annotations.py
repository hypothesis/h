import datetime
import random

import click


@click.command()
@click.pass_context
@click.option("--number", default=100)
def create_annotations(ctx, number):
    from tests.common import factories

    request = ctx.obj["bootstrap"]()
    db = request.db
    tm = request.tm

    for _ in range(number):
        created = updated = datetime.datetime(  # noqa: DTZ001
            year=random.randint(2015, 2020),  # noqa: S311
            month=random.randint(1, 12),  # noqa: S311
            day=random.randint(1, 27),  # noqa: S311
            hour=random.randint(1, 12),  # noqa: S311
            minute=random.randint(0, 59),  # noqa: S311
            second=random.randint(0, 59),  # noqa: S311
        )
        db.add(
            factories.Annotation.build(created=created, updated=updated, shared=True)
        )

    tm.commit()

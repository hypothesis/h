import datetime
import random

import click

from tests.common import factories


@click.command()
@click.pass_context
@click.option("--number", default=100)
def create_annotations(ctx, number):
    request = ctx.obj["bootstrap"]()
    db = request.db
    tm = request.tm

    for _ in range(number):
        created = updated = datetime.datetime(
            year=random.randint(2015, 2020),
            month=random.randint(1, 12),
            day=random.randint(1, 27),
            hour=random.randint(1, 12),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        db.add(
            factories.Annotation.build(created=created, updated=updated, shared=True)
        )

    tm.commit()

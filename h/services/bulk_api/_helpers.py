from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from h.services.bulk_api.exceptions import BadDateFilter


def date_match(column: InstrumentedAttribute[datetime], spec: dict):
    """
    Get an SQL comparator for a date column based on dict spec.

    The dict can contain operators as keys and dates as values as per the
    following complete (but nonsensical) filter:

        {
            "gt": "2012-11-30",
            "gte": "2012-11-30",
            "lt": "2012-11-30",
            "lte": "2012-11-30",
            "eq": "2012-11-30",
            "ne": "2012-11-30",
        }

    :raises BadDateFilter: For unrecognised operators or no spec
    """
    if not spec:
        raise BadDateFilter(f"No spec given to filter '{column}' on")  # noqa: EM102, TRY003

    clauses = []

    for op_key, value in spec.items():
        if op_key == "gt":
            clauses.append(column > value)
        elif op_key == "gte":
            clauses.append(column >= value)
        elif op_key == "lt":
            clauses.append(column < value)
        elif op_key == "lte":
            clauses.append(column <= value)
        elif op_key == "eq":
            clauses.append(column == value)
        elif op_key == "ne":
            clauses.append(column != value)
        else:
            raise BadDateFilter(f"Unknown date filter operator: {op_key}")  # noqa: EM102, TRY003

    return sa.and_(*clauses)

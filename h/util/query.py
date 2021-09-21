"""Database query utilities."""
import sqlalchemy as sa


def column_windows(session, column, windowsize=2000, where=None):
    """
    Return a series of WHERE clauses against a given column that break it into windows.

    :param session: the SQLAlchemy session object
    :param column: the SQLAlchemy column object with which to generate windows
    :param windowsize: how many rows to include in each window
    :param where: an optional SQLAlchemy expression to filter the base query

    Returns an iterable of SQLAlchemy expressions which can be used in a
    .filter(...) clause.
    """

    # This function is adapted from a recipe supplied by the SQLAlchemy
    # maintainers:
    #
    #   https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/WindowedRangeQuery
    #
    # In overview: we generate a list of all the possible values of `column`
    # on the server, and then turn that list into a subquery with
    # Query#from_self(). We then use the row number of the inner query to
    # select every `windowsize`'th row. The resulting values are then
    # translated into an iterable of SQLAlchemy expressions suitable for use
    # in Query#filter(...).

    def interval_for_range(start_id, end_id):
        if end_id:
            return sa.and_(column >= start_id, column < end_id)

        return column >= start_id

    query = session.query(
        column, sa.func.row_number().over(order_by=column).label("rownum")
    )

    if where is not None:
        query = query.filter(where)

    query = query.from_self(column)

    # Select every "windowsize'th" row from the inner query.
    if windowsize > 1:
        query = query.filter(
            sa.text(
                "rownum %% %d=1" % windowsize  # pylint:disable=consider-using-f-string
            )
        )

    intervals = [id for id, in query]

    while intervals:
        start = intervals.pop(0)
        if intervals:
            end = intervals[0]
        else:
            end = None
        yield interval_for_range(start, end)

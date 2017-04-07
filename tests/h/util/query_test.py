# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import string

import pytest

import sqlalchemy as sa

from h.util.query import column_windows


meta = sa.MetaData()

test_cw = sa.Table(
    'test_column_windows',
    meta,
    sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
    sa.Column('name', sa.UnicodeText, nullable=False),
    sa.Column('enabled', sa.Boolean, nullable=False),
)


@pytest.mark.usefixtures('cw_table')
class TestColumnWindows(object):

    @pytest.mark.parametrize('windowsize,expected', [
        (100, ['abcdefghijklmnopqrstuvwxyz']),
        (26, ['abcdefghijklmnopqrstuvwxyz']),
        (13, ['abcdefghijklm', 'nopqrstuvwxyz']),
        (10, ['abcdefghij', 'klmnopqrst', 'uvwxyz']),
        (5, ['abcde', 'fghij', 'klmno', 'pqrst', 'uvwxy', 'z']),
        (1, [l for l in string.lowercase]),
    ])
    def test_basic_windowing(self, db_session, windowsize, expected):
        """Check that windowing returns the correct batches of rows."""
        testdata = [{'name': l, 'enabled': True}
                    for l in string.lowercase]
        db_session.execute(test_cw.insert().values(testdata))

        windows = column_windows(db_session,
                                 test_cw.c.name,
                                 windowsize=windowsize)

        assert window_query_results(db_session, windows) == expected

    @pytest.mark.parametrize('windowsize,expected', [
        (100, ['abcdefghijklm']),
        (13, ['abcdefghijklm']),
        (10, ['abcdefghij', 'klm']),
        (3, ['abc', 'def', 'ghi', 'jkl', 'm']),
        (1, [l for l in string.lowercase[:13]]),
    ])
    def test_filtered_windowing(self, db_session, windowsize, expected):
        """Check that windowing respects the where clause."""
        testdata = []
        enabled = string.lowercase[:13]
        disabled = string.lowercase[13:]
        testdata.extend([{'name': l, 'enabled': True} for l in enabled])
        testdata.extend([{'name': l, 'enabled': False} for l in disabled])
        db_session.execute(test_cw.insert().values(testdata))

        filter_ = test_cw.c.enabled
        windows = column_windows(db_session,
                                 test_cw.c.name,
                                 windowsize=windowsize,
                                 where=filter_)

        assert window_query_results(db_session, windows, filter_) == expected


def window_query_results(session, windows, filter_=None):
    """
    Fetch results using the passed windows and optional filter.

    Returns a list of strings which represent the rows returned by each
    window.
    """
    results = []
    for window in windows:
        part = session.query(test_cw.c.name).filter(window)
        if filter_ is not None:
            part = part.filter(filter_)
        results.append(''.join(row.name for row in part))
    return results


@pytest.yield_fixture
def cw_table(db_engine):
    test_cw.create(db_engine)
    yield
    test_cw.drop(db_engine)

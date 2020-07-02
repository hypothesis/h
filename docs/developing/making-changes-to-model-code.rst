============================
Making changes to model code
============================


---------------------------------
Guidelines for writing model code
---------------------------------

No length limits on database columns
====================================

Don't put any length limits on your database columns (for example
``sqlalchemy.Column(sqlalchemy.Unicode(30), ...)``). These can cause painful
database migrations.

Always use ``sqlalchemy.UnicodeText()`` with no length limit as the type for
text columns in the database (you can also use ``sqlalchemy.Text()`` if you're
sure the column will never receive non-ASCII characters).

When necessary validate the lengths of strings in Python code instead.
This can be done using `SQLAlchemy validators <http://docs.sqlalchemy.org/en/rel_1_0/orm/mapped_attributes.html>`_
in model code.

View callables for HTML forms should also use Colander schemas to validate user
input, in addition to any validation done in the model code, because Colander
supports returning per-field errors to the user.


------------------------------------
Creating a database migration script
------------------------------------

If you've made any changes to the database schema (for example: added or
removed a SQLAlchemy ORM class, or added, removed or modified a
``sqlalchemy.Column`` on an ORM class) then you need to create a database
migration script that can be used to upgrade the production database from the
previous to your new schema.

We use `Alembic <https://alembic.readthedocs.io/en/latest/>`_ to create and run
migration scripts. See the Alembic docs (and look at existing scripts in
`h/migrations/versions <https://github.com/hypothesis/h/tree/master/h/migrations/versions>`_)
for details. The ``make db`` command is a wrapper around Alembic. The
steps to create a new migration script for h are:

1. Create the revision script by running ``makge db args=revision``, for example:

   .. code-block:: bash

      make db args='revision -m "Add the foobar table"'

   This will create a new script in ``h/migrations/versions/``.

2. Edit the generated script, fill in the ``upgrade()`` and ``downgrade()``
   methods.

   See https://alembic.readthedocs.io/en/latest/ops.html#ops for details.

   .. note::

      Not every migration should have a ``downgrade()`` method. For example if
      the upgrade removes a max length constraint on a text field, so that
      values longer than the previous max length can now be entered, then a
      downgrade that adds the constraint back may not work with data created
      using the updated schema.

3. Test your ``upgrade()`` function by upgrading your database to the most
   recent revision. This will run all migration scripts newer than the revision
   that your db is currently stamped with, which usually means just your new
   revision script:

   .. code-block:: bash

      make db

   After running this command inspect your database's schema to check that it's
   as expected, and run h to check that everything is working.

   .. note::

      You should make sure that there's some repesentative data in the relevant
      columns of the database before testing upgrading and downgrading it.
      Some migration script crashes will only happen when there's data present.

4. Test your ``downgrade()`` function:

   .. code-block:: bash

      make db args='downgrade -1'

   After running this command inspect your database's schema to check that it's
   as expected. You can then upgrade it again:

   .. code-block:: bash

      make db args='upgrade +1'

Batch deletes and updates in migration scripts
==============================================

It's important that migration scripts don't lock database tables for too long,
so that when the script is run on the production database concurrent database
transactions from web requests aren't held up.

An SQL ``DELETE`` command acquires a ``FOR UPDATE`` row-level lock on the
rows that it selects to delete. An ``UPDATE`` acquires a ``FOR UPDATE`` lock on
the selected rows *if the update modifies any columns that have a unique index
on them that can be used in a foreign key*. While held this ``FOR UPDATE`` lock
prevents any concurrent transactions from modifying or deleting the selected
rows.

So if your migration script is going to ``DELETE`` or ``UPDATE`` a large number
of rows at once and committing that transaction is going to take a long time
(longer than 100ms) then you should instead do multiple ``DELETE``\s or
``UPDATE``\s of smaller numbers of rows, committing each as a separate
transaction. This will allow concurrent transactions to be sequenced in-between
your migration script's transactions.

For example, here's some Python code that deletes all the rows that match a
query in batches of 25:

.. code-block:: python

   query = <some sqlalchemy query>
   query = query.limit(25)
   while True:
       if query.count() == 0:
           break
       for row in query:
           session.delete(row)
       session.commit()

Separate data and schema migrations
===================================

It's easier for deployment if you do *data migrations* (code that creates,
updates or deletes rows) and *schema migrations* (code that modifies the
database *schema*, for example adding a new column to a table) in separate
migration scripts instead of combining them into one script. If you have a
single migration that needs to modify some data and then make a schema change,
implement it as two consecutive migration scripts instead.

Don't import model classes into migration scripts
=================================================

Don't import model classes, for example ``from h.models import Annotation``,
in migration scripts. Instead copy and paste the ``Annotation`` class into your
migration script.

This is because the script needs the schema of the ``Annotation`` class
as it was at a particular point in time, which may be different from the
schema in ``h.models.Annotation`` when the script is run in the future.

The script's copy of the class usually only needs to contain the definitions of
the primary key column(s) and any other columns that the script uses, and only
needs the name and type attributes of these columns. Other attributes of the
columns, columns that the script doesn't use, and methods can usually be left
out of the script's copy of the model class.

Troubleshooting migration scripts
=================================

(sqlite3.OperationalError) near "ALTER"
---------------------------------------

SQLite doesn't support ``ALTER TABLE``. To get around this, use
`Alembic's batch mode <https://alembic.readthedocs.io/en/latest/batch.html>`_.


Cannot add a NOT NULL column with default value NULL
----------------------------------------------------

If you're adding a column to the model with ``nullable=False`` then when the
database is upgraded it needs to insert values into this column for each of
the already existing rows in the table, and it can't just insert ``NULL`` as it
normally would. So you need to tell the database what default value to insert
here.

``default=`` isn't enough (that's only used when the application is creating
data, not when migration scripts are running), you need to add a
``server_default=`` argument to your ``add_column()`` call.

See the existing migration scripts for examples.

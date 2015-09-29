============================
Making Changes to Model Code
============================


---------------------------------
Guidelines for Writing Model Code
---------------------------------

No Length Limits on Database Columns
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
Creating a Database Migration Script
------------------------------------

If you've made any changes to the database schema (for example: added or
removed a SQLAlchemy ORM class, or added, removed or modified a
``sqlalchemy.Column`` on an ORM class) then you need to create a database
migration script that can be used to upgrade the production database from the
previous to your new schema.

We use `Alembic <http://alembic.readthedocs.org/en/latest/>`_ to create and run
migration scripts. See the Alembic docs (and look at existing scripts in
`h/migrations/versions <https://github.com/hypothesis/h/tree/master/h/migrations/versions>`_)
for details, but the basic steps to create a new migration script for h are:

1. Create the revision script by running ``alembic revision``, for example:

   .. code-block:: bash

      alembic -c conf/alembic.ini revision -m "add the foobar table"

   This will create a new script in ``h/migrations/versions/``.

2. Edit the generated script, fill in the ``upgrade()`` and ``downgrade()``
   methods.

   See http://alembic.readthedocs.org/en/latest/ops.html#ops for details.

   .. note::

      Not every migration should have a ``downgrade()`` method. For example if
      the upgrade removes a max length constraint on a text field, so that
      values longer than the previous max length can now be entered, then a
      downgrade that adds the constraint back may not work with data created
      using the updated schema.

3. Stamp your database.

   Before running any upgrades or downgrades you need to stamp the database
   with its current revision, so Alembic knows which migration scripts to run:

   .. code-block:: bash

      alembic -c conf/alembic.ini stamp <revision_id>

   ``<revision_id>`` should be the revision corresponding to the version of the
   code that was present when the current database was created. The will
   usually be the ``down_revision`` from the migration script that you've just
   generated.

4. Test your ``upgrade()`` function by upgrading your database to the most
   recent revision. This will run all migration scripts newer than the revision
   that your db is currently stamped with, which usually means just your new
   revision script:

   .. code-block:: bash

      alembic -c conf/alembic.ini upgrade head

   After running this command inspect your database's schema to check that it's
   as expected, and run h to check that everything is working.

   .. note::

      You should make sure that there's some repesentative data in the relevant
      columns of the database before testing upgrading and downgrading it.
      Some migration script crashes will only happen when there's data present.

5. Test your ``downgrade()`` function:

   .. code-block:: bash

      alembic -c conf/alembic.ini downgrade -1

   After running this command inspect your database's schema to check that it's
   as expected. You can then upgrade it again:

   .. code-block:: bash

      alembic -c conf/alembic.ini upgrade +1


Troubleshooting Migration Scripts
=================================

(sqlite3.OperationalError) near "ALTER"
---------------------------------------

SQLite doesn't support ``ALTER TABLE``. To get around this, use
`Alembic's batch mode <https://alembic.readthedocs.org/en/latest/batch.html>`_.


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

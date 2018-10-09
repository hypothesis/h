Accessing the admin interface
-----------------------------

To access the admin interface, a user must be logged in and have admin
permissions. To grant admin permissions to a user, run the following command:

.. code-block:: bash

  tox -e py27-dev -- sh bin/hypothesis --dev user admin <username>

For example, to make the user 'joe' an admin in the development environment:

.. code-block:: bash

  tox -e py27-dev -- sh bin/hypothesis --dev user admin joe

When this user signs in they can now access the adminstration panel at
``/admin``. The administration panel has options for managing users and optional
features.

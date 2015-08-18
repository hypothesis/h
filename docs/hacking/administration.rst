Administration
--------------

To access the admin interface, a user must be logged in and have admin
permissions. To grant admin permissions to a user, run the following command:

.. code-block:: bash

  hypothesis admin <config_uri> <username>

For example, to make someone an admin in the development environment:

.. code-block:: bash

  hypothesis admin conf/development.ini usernamehere

When this user signs in they can now access the adminstration panel at
``/admin``. The administration panel has options for managing users and optional
features.

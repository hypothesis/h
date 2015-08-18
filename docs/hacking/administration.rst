Administration
--------------

To access the admin interface, a user must be logged into hypothes.is and have admin permissions.
To grant admin permissions to a user, run the following command in the virtual environment:

.. code-block:: bash
	
	hypothesis admin <config_uri> <username>

For example, to make someone an admin in the development configuration:
	
.. code-block:: bash
	
	hypothesis admin conf/development.ini usernamehere

When this user signs in they can now access the adminstration panel at ``/admin``. The administration panel has basic options for managing users, as well as the ability to enable feature flags to try out features currently in development.


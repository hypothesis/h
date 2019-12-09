Accessing the admin interface
-----------------------------

To access the admin interface, a user must be logged in and have admin
permissions. To grant admin permissions to a user, first create a user, 
or use an existing one, and then promote that user to be an ``admin``:

**Create the user (if needed)**

.. code-block:: bash

  tox -qe dev -- sh bin/hypothesis --dev user add

This will prompt you to enter the user's 

  #. unique name
  #. unique email address
  #. password

Once you have entered that information, then you may promote the 
user to ``admin``.

**Promote to admin level**

.. note::

    Replace ``<username>`` with the value you entered in the previous step
    or appropriate user's name.


.. code-block:: bash

  tox -qe dev -- sh bin/hypothesis --dev user admin <username>

When this user signs in they can now access the administration panel at
``/admin``. The administration panel has options for managing users and optional
features.

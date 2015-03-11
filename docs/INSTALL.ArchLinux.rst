Installing Hypothesis on ArchLinux
##################################

Install the following packages:

.. code-block:: bash

    python2-pip python2-virtualenv libyaml gcc git nodejs libffi

From the Arch User Repository (AUR), obtain:

.. code-block:: bash

    elasticsearch ruby-compass

Then follow the general instructions for all platforms.

.. note::

    The project does not run under Python 3 at this time. It is
    recommended to build the project under a Python 2 virtual
    environment.

.. code-block:: bash

    systemctl start elasticsearch.service

Everything should be ready!

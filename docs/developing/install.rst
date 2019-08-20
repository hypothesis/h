Installing h in a development environment
=========================================

The code for the https://hypothes.is/ web service and API lives in a
`Git repo named h`_. This page will walk you through getting this code running
in a local development environment.

.. seealso::

   * https://github.com/hypothesis/client/ for installing the Hypothesis client
   * https://github.com/hypothesis/browser-extension. for the browser extension
   * To get "direct" or "in context" links working you need to install Bouncer and Via:\ 

     * https://github.com/hypothesis/bouncer
     * https://github.com/hypothesis/via

.. seealso::

   :doc:`troubleshooting` if you run into any problems during installation

You will need
-------------

Before installing your local development environment you'll need to install
each of these prerequisites:

* `Git <https://git-scm.com/>`_

* `Node <https://nodejs.org/>`_ and npm.
  On Linux you should follow
  `nodejs.org's instructions for installing node <https://nodejs.org/en/download/package-manager/>`_
  because the version of node in the standard Ubuntu package repositories is
  too old.
  On macOS you should use `Homebrew <https://brew.sh/>`_ to install node.

* `Docker <https://docs.docker.com/install/>`_.
  Follow the `instructions on the Docker website <https://docs.docker.com/install/>`_
  to install "Docker Engine - Community".

* `pyenv`_.
  Follow the instructions in the pyenv README to install it.

Clone the Git repo
------------------

.. code-block:: shell

   git clone https://github.com/hypothesis/h.git

This will download the code into an ``h`` directory in your current working
directory. You need to be in the ``h`` directory from the remainder of the
installation process:

.. code-block:: shell

   cd h

Run the services with Docker Compose
------------------------------------

Start the services that h requires using Docker Compose:

.. code-block:: shell

   make services

You'll now have some Docker containers running the PostgreSQL, RabbitMQ, and
Elasticsearch services. You should be able to see them by running
``make services args=ps``. You should also be able to visit your Elasticsearch
service by opening http://localhost:9200/ in a browser, and connect to your
PostgreSQL by running ``make sql``.

Start the development server
----------------------------

.. code-block:: shell

    make dev

The first time you run ``make dev`` it might take a while to start because
it'll need to install the application dependencies and build the client assets.

This will start the server on port 5000 (http://localhost:5000), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

**That's it!** You've finished setting up your h development environment.
Run ``make help`` to see all the commands that're available for running the
tests, linting, code formatting, Python and SQL shells, etc.

.. _Git repo named h: https://github.com/hypothesis/h/
.. _pyenv: https://github.com/pyenv/pyenv

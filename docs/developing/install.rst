Website dev install
===================

The code for the https://hypothes.is/ website and API lives in a
`Git repo named h`_. To get this code running in a local development
environment the first thing you need to do is install h's system dependencies.

.. seealso::

   This page documents how to setup a development install of h.
   For installing the Hypothesis client for development see
   https://github.com/hypothesis/client/, and for the browser extension
   see https://github.com/hypothesis/browser-extension.

Follow either the
`Installing the system dependencies on Ubuntu`_ or the
`Installing the system dependencies on macOS`_ section below, depending on which
operating system you're using, then move on to `Getting the h source code from GitHub`_ and
the sections that follow it.


Installing the system dependencies on Ubuntu
--------------------------------------------

This section describes how to install h's system dependencies on Ubuntu.
These steps will also probably work with few or no changes on other versions
of Ubuntu, Debian, or other Debian-based GNU/Linux distributions.

Install the following packages:

.. code-block:: bash

    sudo apt-get install -y --no-install-recommends \
        build-essential \
        git \
        tox \
        libevent-dev \
        libffi-dev \
        libfontconfig \
        libpq-dev \
        libssl-dev \
        python-dev \
        python-pip

Install node by following the
`instructions on nodejs.org <https://nodejs.org/en/download/package-manager/>`_
(the version of the nodejs package in the standard Ubuntu repositories is too
old).

Upgrade pip and npm:

.. code-block:: bash

    sudo pip install -U pip
    sudo npm install -g npm


Installing the system dependencies on macOS
-------------------------------------------

This section describes how to install h's system dependencies on macOS.

The instructions that follow assume you have previously installed Homebrew_.

.. _Homebrew: http://brew.sh/

Install the following packages:

.. code-block:: bash

    brew install \
        libevent \
        libffi \
        node \
        postgresql \
        python \
        tox

.. note:: Unfortunately you need to install the ``postgresql`` package, because
          Homebrew does not currently provide a standalone ``libpq`` package.

Upgrade pip:

.. code-block:: bash

    pip install -U pip

Getting the h source code from GitHub
-------------------------------------

Use ``git`` to download the h source code:

.. code-block:: bash

    git clone https://github.com/hypothesis/h.git

This will download the code into an ``h`` directory in your current working
directory.

Change into the ``h`` directory from the remainder of the installation
process:

.. code-block:: bash

   cd h


Installing the services
-----------------------

h requires the following external services:

- PostgreSQL_ 9.4+
- Elasticsearch_ v6, with the `Elasticsearch ICU Analysis`_ plugin
- RabbitMQ_ v3.5+

.. _PostgreSQL: http://www.postgresql.org/
.. _Elasticsearch: https://www.elastic.co/
.. _Elasticsearch ICU Analysis: https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html
.. _RabbitMQ: https://rabbitmq.com/

You can install these services however you want, but the easiest way is by using
Docker and Docker Compose. This should work on any operating system that Docker
can be installed on:

1. Install Docker and Docker Compose by following the instructions on the
   `Docker website`_.

2. Run Docker Compose:

   .. code-block:: bash

      docker-compose up

   You'll now have some Docker containers running the PostgreSQL, RabbitMQ, and
   Elasticsearch services. You should be able to see them by running ``docker
   ps``. You should also be able to visit your Elasticsearch service by opening
   http://localhost:9200/ in a browser, and connect to your PostgreSQL by
   running ``psql postgresql://postgres@localhost/postgres`` (if you have psql
   installed).

   .. note::

      If at any point you want to shut the containers down, you can
      interrupt the ``docker-compose`` command. If you want to run the
      containers in the background, you can run ``docker-compose up -d``.

3. Create the `htest` database in the ``postgres`` container. This is needed
   to run the h tests:

   .. code-block:: bash

      docker-compose exec postgres psql -U postgres -c "CREATE DATABASE htest;"


.. tip::

   You can use Docker Compose image to open a psql shell in your Dockerized
   database container without having to install psql on your host machine. Do:

   .. code-block:: bash

      docker-compose exec postgres psql -U postgres

.. tip::

   Use the ``docker-compose logs`` command to see what's going on inside your
   Docker containers, for example:

   .. code-block:: bash

      docker-compose logs rabbit

   For more on how to use Docker and Docker Compose see the `Docker website`_.


.. _Docker website: https://docs.docker.com/compose/install/


Installing the gulp command
---------------------------

Install ``gulp-cli`` to get the ``gulp`` command:

.. code-block:: bash

    sudo npm install -g gulp-cli


Running h
---------

Start a development server:

.. code-block:: bash

    make dev

The first time you run ``make dev`` it might take a while to start because
it'll need to install the application dependencies and build the client assets.

This will start the server on port 5000 (http://localhost:5000), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.


.. _running-the-tests:

Running h's tests
-----------------

There are test suites for both the frontend and backend code. To run the
complete set of tests, run:

.. code-block:: bash

    make test

To run the frontend test suite only, run the appropriate test task with gulp.
For example:

.. code-block:: bash

    gulp test

When working on the front-end code, you can run the Karma test runner in
auto-watch mode which will re-run the tests whenever a change is made to the
source code. To start the test runner in auto-watch mode, run:

.. code-block:: bash

    gulp test-watch

To run only a subset of tests for front-end code, use the ``--grep``
argument or mocha's `.only()`_ modifier.

.. code-block:: bash

    gulp test-watch --grep <pattern>

.. _.only(): http://jaketrent.com/post/run-single-mocha-test/


Debugging h
-----------

The `pyramid_debugtoolbar`_ package is loaded by default in the development
environment.  This will provide stack traces for exceptions and allow basic
debugging. A more advanced profiler can also be accessed at the /_debug_toolbar
path.

    http://localhost:5000/_debug_toolbar/

Check out the `pyramid_debugtoolbar documentation`_ for information on how to
use and configure it.

.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. _pyramid_debugtoolbar documentation: http://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/

You can turn on SQL query logging by setting the ``DEBUG_QUERY``
environment variable (to any value). Set it to the special value ``trace`` to
turn on result set logging as well.


Feature flags
-------------

Features flags allow admins to enable or disable features for certain groups
of users. You can enable or disable them from the Administration Dashboard.

To access the Administration Dashboard, you will need to first create a
user account in your local instance of H and then give that account
admin access rights using H's command-line tools.

See the :doc:`/developing/administration` documentation for information
on how to give the initial user admin rights and access the Administration
Dashboard.

Troubleshooting
---------------

Cannot connect to the Docker daemon
```````````````````````````````````

If you get an error that looks like this when trying to run ``docker``
commands::

 Cannot connect to the Docker daemon. Is the docker daemon running on this host?
 Error: failed to start containers: postgres

it could be because you don't have permission to access the Unix socket that
the docker daemon is bound to. On some operating systems (e.g. Linux) you need
to either:

* Take additional steps during Docker installation to give your Unix user
  access to the Docker daemon's port (consult the installation
  instructions for your operating system on the `Docker website`_), or

* Prefix all ``docker`` commands with ``sudo``.


.. _Git repo named h: https://github.com/hypothesis/h/

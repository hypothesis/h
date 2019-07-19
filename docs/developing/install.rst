Installing h in a development environment
=========================================

The code for the https://hypothes.is/ web service and API lives in a
`Git repo named h`_. This page will walk you through getting this code running
in a local development environment.

.. seealso::

   This page documents how to setup a development install of h.
   For installing the Hypothesis client for development see
   https://github.com/hypothesis/client/, and for the browser extension
   see https://github.com/hypothesis/browser-extension.

   To get "direct" or "in context" links working you need to install Bouncer
   and Via. See https://github.com/hypothesis/bouncer and
   https://github.com/hypothesis/via.

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

* `Gulp <https://gulpjs.com/>`_.
  Once you have npm you can just run ``sudo npm install -g gulp-cli`` to install ``gulp``.
  On macOS it's recommended to run ``npm install -g gulp-cli`` without the ``sudo``.

* `Docker CE <https://docs.docker.com/install/>`_ and `Docker Compose <https://docs.docker.com/compose/>`_.
  Follow the `instructions on the Docker website <https://docs.docker.com/compose/install/>`_
  to install these.


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
Elasticsearch services. You should be able to see them by running ``docker-compose
ps``. You should also be able to visit your Elasticsearch service by opening
http://localhost:9200/ in a browser, and connect to your PostgreSQL by
running ``docker-compose exec postgres psql -U postgres``.

Use pyenv to install Python and tox
-----------------------------------

Install Python 2.7 and 3.6 in pyenv and install tox in each:

.. code-block:: shell

   pyenv install 2.7.16
   pyenv install 3.6.8
   pyenv shell 2.7.16
   pip install tox>=3.8.0
   pyenv shell 3.6.8
   pip install tox>=3.8.0
   pyenv shell --unset

Start the development server
----------------------------

.. code-block:: shell

    make dev

The first time you run ``make dev`` it might take a while to start because
it'll need to install the application dependencies and build the client assets.

This will start the server on port 5000 (http://localhost:5000), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

Troubleshooting
---------------

Cannot connect to the Docker daemon
###################################

If you get an error that looks like this when trying to run ``docker``
commands::

 Cannot connect to the Docker daemon. Is the docker daemon running on this host?
 Error: failed to start containers: postgres

it could be because you don't have permission to access the Unix socket that
the docker daemon is bound to. On some operating systems (e.g. Linux) you need
to either:

* Take additional steps during Docker installation to give your Unix user
  access to the Docker daemon's port (consult the installation
  instructions for your operating system on the Docker website), or

* Prefix all ``docker`` and ``docker-compose`` commands with ``sudo``.


.. _Git repo named h: https://github.com/hypothesis/h/
.. _pyenv: https://github.com/pyenv/pyenv


pyenv errors on macOS
#####################

``pyenv install`` commands might fail on macOS with error messages such as:

* "symbol(s) not found for architecture x86_64"
* "ERROR: The Python zlib extension was not compiled. Missing the zlib?"

Read `pyenv's Common Build Problems page <https://github.com/pyenv/pyenv/wiki/common-build-problems>`_
for the solutions to these.

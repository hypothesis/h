Installing h in a development environment
#########################################

This document contains instructions on setting up a development environment for
h. If you are looking for instructions on deploying h in a production
environment, please consult the :doc:`/INSTALL` instead.


Requirements
------------

To run h in a development environment you'll need these system dependencies
installed:

-  Python_ v2.7
-  Node_ v0.10+ and its package manager, npm
-  Compass_ v1.0+

You'll also need to run, at a minimum, these external services:

-  ElasticSearch_ v1.0+, with the `ElasticSearch ICU Analysis`_ plugin
   installed
-  NSQ_ v0.3+

.. _Python: http://python.org/
.. _Node: http://nodejs.org/
.. _Compass: http://compass-style.org/
.. _ElasticSearch: http://www.elasticsearch.org/
.. _ElasticSearch ICU Analysis: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/analysis-icu-plugin.html
.. _NSQ: http://nsq.io/

The following sections will explain how to install these system dependencies
and services.


Installing the system dependencies
----------------------------------

Installing h's system dependencies is different on different operating systems.
Follow either the
`Installing the system dependencies on Ubuntu 14.04`_ or the
`Installing the system dependencies on OS X`_ section below.


Installing the system dependencies on Ubuntu 14.04
``````````````````````````````````````````````````

This section describes how to install h's system dependencies on Ubuntu 14.04.
These steps will also probably work with little or no changes on other versions
of Ubuntu, Debian, or other Debian-based GNU/Linux distributions.

Install the following packages:

.. code-block:: bash

    sudo apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libevent-dev \
        libffi-dev \
        libpq-dev \
        libyaml-dev \
        nodejs \
        npm \
        python-dev \
        python-pip \
        python-virtualenv \
        ruby \
        ruby-dev

Add a ``node`` symlink. This is needed because the node binary from Ubuntu is
called ``nodejs`` but many packages will try to run it as ``node``:

.. code-block:: bash

    sudo ln -s /usr/bin/nodejs /usr/bin/node

Upgrade pip and npm:

.. code-block:: bash

    sudo pip install -U pip virtualenv
    sudo npm install -g npm

Install compass:

.. code-block:: bash

    sudo gem install compass


Installing the system dependencies on OS X
``````````````````````````````````````````

This section describes how to install h's system dependencies on Mac OS X.

The instructions that follow assume you have previously installed Homebrew_.

.. _Homebrew: http://brew.sh/

Install the following packages:

.. code-block:: bash

    brew install \
        libevent \
        libffi \
        libyaml \
        node \
        python

Install compass:

.. code-block:: bash

    gem install compass


Installing ElasticSearch
------------------------

The h project uses ElasticSearch_ (v1.0 or later) as its principal data store
for annotation data, and requires the `ElasticSearch ICU Analysis`_ plugin to be
installed.

1.  Install ElasticSearch. It is best to follow the instructions provided by the
    ElasticSearch project for `installing the package on your platform`_.
2.  Install the ICU Analysis plugin using the `instructions provided`_. **NB:**
    ensure you install the correct version of the plugin for your version of
    ElasticSearch.
3.  (Re-)start the ElasticSearch daemon following the steps on the ElasticSearch
    `installation page`_. Note that the daemon needs to be restarted after installing
    the ICU plugin.

.. _installing the package on your platform: https://www.elastic.co/downloads/elasticsearch
.. _instructions provided: https://github.com/elastic/elasticsearch-analysis-icu#icu-analysis-for-elasticsearch
.. _installation page: https://www.elastic.co/downloads/elasticsearch


ElasticSearch Troubleshooting
`````````````````````````````

By default, ElasticSearch may try to join other nodes on the network resulting
in ``IndexAlreadyExists`` errors at startup. See the documentation for how to
turn off discovery.


Installing NSQ
--------------

The NSQ homepage has `instructions on installing NSQ`_. Once installed,
running ``nsqd`` in its default configuration should suffice for integration
with h in a development environment.

.. _instructions on installing NSQ: http://nsq.io/deployment/installing.html


Get the h source code from GitHub
---------------------------------

Use ``git`` to download the h source code:

.. code-block:: bash

    git clone https://github.com/hypothesis/h.git

This will download the code into an ``h`` directory in your current working
directory.


Install h into a Python virtualenv
----------------------------------

Although it is strictly optional, we highly recommend that you install h inside
a Python "virtualenv". First, follow the instructions for your platform on
installing virtualenvwrapper_. Then, at a shell, you can create a virtualenv for
the h application with:

.. code-block:: bash

    mkvirtualenv h

You will notice that the your shell prompt changes to include a (h) symbol. That
means that you now have your virtual environment activated. This is required for
running the code.

At any later time, you can activate your virtualenv by running:

.. code-block:: bash

    workon h

Install h's Python dependencies into the virtual environment, and its Node
dependencies into the ``h/node_modules`` directory:

.. code-block:: bash

    cd h
    make deps

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/install.html

Running h
---------

Now that you've installed h and all of its dependencies, you should be able to
run h in your development environment with this command:

.. code-block:: bash

    make dev

This will start the server on port 5000 (http://localhost:5000), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

.. note::
    Using the bookmarklet or otherwise embedding the application may not
    be possible on sites accessed via HTTPS due to browser policy restricting
    the inclusion of non-SSL content.

.. _running-the-tests:

Running the tests
-----------------

There are test suites for both the frontend and backend code.

To run the complete set of tests, run:

.. code-block:: bash

    make test

To run the frontend test suite only, run:

.. code-block:: bash

    make client-test

When working on the front-end code, you can run the Karma test runner in auto-watch
mode which will re-run the tests whenever a change is made to the source code.
To start the test runner in auto-watch mode, run:

.. code-block:: bash

    make client-test-watch

You can further speed up the testing cycle for front-end code by using
mocha's `.only()`_ to only run a particular suite of tests or even just
a single test.

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


Feature Flags
-------------

Features flags allow admins to enable or disable features for certain groups
of users. You can enable or disable them from the Administration Dashboard.

To access the Administration Dashboard, you will need to first create a
user account in your local instance of H and then give that account
admin access rights using H's command-line tools.

See the :doc:`../administration` documentation for information
on how to give the initial user admin rights and access the Administration
Dashboard.


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
`Installing the system dependencies on Debian or Ubuntu`_ or the
`Installing the system dependencies on OS X`_ section below.


Installing the system dependencies on Debian or Ubuntu
``````````````````````````````````````````````````````

This section describes how to install h's system dependencies on Debian and
Debian-like GNU/Linux distributions (such as Ubuntu).

Not all required packages are necessarily part of the ``stable`` distribution;
you may need to fetch some stuff from ``unstable``. (On Ubuntu, you may need to
add the ``universe`` package repositories.)

Install the following packages::

    $ apt-get -y --no-install-recommends \
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

Upgrade pip and npm::

    $ pip install -U pip virtualenv
    $ npm install -g npm

Install compass::

    $ gem install compass


Installing the system dependencies on OS X
``````````````````````````````````````````

This section describes how to install h's system dependencies on Mac OS X.

The instructions that follow assume you have previously installed Homebrew_.

.. _Homebrew: http://brew.sh/

Install the following packages::

    $ brew install \
        libevent \
        libffi \
        libyaml \
        node \
        python

Install compass::

    $ gem install compass


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

.. _installing the package on your platform: https://www.elastic.co/downloads/elasticsearch
.. _instructions provided: https://github.com/elastic/elasticsearch-analysis-icu#icu-analysis-for-elasticsearch


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


Install h into a Python virtualenv
----------------------------------

Although it is strictly optional, we highly recommend that you install h inside
a Python "virtualenv". First, follow the instructions for your platform on
installing virtualenvwrapper_. Then, at a shell, you can create a virtualenv for
the h application with::

    $ mkvirtualenv h  

You will notice that the your shell prompt changes to include a (h) symbol. That
means that you now have your virtual environment activated. This is required for
running the code.

At any later time, you can activate your virtualenv by running::

    $ workon h

Once platform dependencies are installed::

    $ make deps

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/install.html


Running h
---------

Now that you've installed h and all of its dependencies, you should be able to
run h in your development environment with this command::

    $ make dev

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

To run the Python suite, invoke the tests in the standard fashion::

    $ python setup.py test

To run the JavaScript suite, run::

    $ $(npm bin)/karma start h/static/scripts/karma.config.js --single-run

As a convenience, there is a make target which will do all of the above::

    $ make test


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


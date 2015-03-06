Hypothesis
==========

.. image:: https://travis-ci.org/hypothesis/h.svg?branch=master
   :target: https://travis-ci.org/hypothesis/h
   :alt: Build Status
.. image:: https://landscape.io/github/hypothesis/h/master/landscape.svg?style=flat
   :target: https://landscape.io/github/hypothesis/h/master
   :alt: Code Health

About
-----

Hypothesis brings community peer review to The Internet. It is a web
application which enables rich annotation of web content. The project acts as
a community aggregator for annotations and identity provider [*]_ for
annotators. It also serves embed code for an annotation agent designed with
modern web browsers in mind.

Installation
------------

See `<INSTALL.rst>`_ for installation instructions. Platform specific
instructions can be found in the install documents as well.

The short version::

    $ # install dependencies
    $ ./bootstrap
    $ ./run


Running
-------

To run the server in development mode, simply use the ``run`` command::

    $ ./run

This will start the server on port 5000 (http://localhost:5000),
reload the application whenever changes are made to the source code, and
restart it should it crash for some reason.

.. note::
    Using the bookmarklet or otherwise embedding the application may not
    be possible on sites accessed via HTTPS due to browser policy restricting
    the inclusion of non-SSL content. If you wish to test the development server
    with these sites uncomment the line beginning with "certfile" in the
    development server configuration file, "development.ini". This will cause
    the server to use a self-signed certificate included for testing.

Development
-----------

The project builds heavily on components developed for the `Annotator Project`_
and is structured to encourage upstream contribution where possible. However,
work is required to make Annotator more extensible in order to facilitate
contribution.

Additionally, work is underway to support the data model described by the
`Open Annotation Core`_ specification document.

Join us in `#hypothes.is`_ on freenode_ for discussion.

If you'd like to contribute to the project should also `subscribe`_ to the
`development mailing list`_ and read about `contributing`_. Then consider getting
started on one of the issues that are ready for work. Issues tagged with the
label '`New Contributor Friendly`_' are ideal for those just getting started.

Debugging
---------

The `pyramid_debugtoolbar`_ package is loaded by default in the development
environment.  This will provide stack traces for exceptions and allow basic
debugging. A more advanced profiler can also be accessed at the /_debug_toolbar
path.

    http://localhost:5000/_debug_toolbar/

Check out the `pyramid_debugtoolbar documentation`_ for information on how to
use and configure it.

Code Quality
------------

We run a variety of analysis tools on the python codebase using the prospector
package. This is run by the CI on each push but can also be run manually
via the ``lint`` make command::

    $ make lint

Our linting is set to low by default. However, if you'd like to help dust it
off a but more, you can run the ``prospector`` command directly and add the
``-s medium`` to get more nagging results from pep8, pylint, etc.

Additionally, we'd love help spiffing up our docstrings! You can give those a
detailed look (and scrub!) by running::

    $ ./bin/pep257 h

Or...for your own sanity, you can pass it the name of a specific file, instead
of ``h`` (ex: ``h/api.py``).

Testing
-------

There are test suites for both the front- and back-end code.

To run the Python suite, invoke the tests in the standard fashion::

    $ ./bin/python setup.py test

To run the JavaScript suite, run::

    $ $(npm bin)/karma start karma.config.js --single-run

As a convenience, there is a make target which will do all of the above::

    $ make test

It's also possible to run a subset of the tests using ``karma run``::

    $ $(npm bin)/karma start karma.config.js & # Start the server in the bg.
    $ $(npm bin)/karma run karma.config.js -- --grep={FILTER_STRING}

This will run generally be much faster than running ``karma start --single-run``
each time. The frontend tests can also be debugged by visiting
http://localhost:9876/debug.html and opening the browser console.

Browser Extensions
^^^^^^^^^^^^^^^^^^
Run the following command at the prompt to build the Chrome extension::

    $ hypothesis-buildext development.ini chrome

Or, to load the assets from within the extension::

    $ hypothesis-buildext development.ini chrome --base http://localhost:5000 --assets chrome-extension://extensionid/public

To build an extension with a feature flag enabled use the environment variable::

    $ FEATURE_NOTIFICATION=true hypothesis-buildext production.ini chrome --base https://hypothes.is --assets chrome-extension://extensionid/public

To build the Firefox extension, run the following::

    $ hypothesis-buildext development.ini firefox --base http://localhost:5000 --assets resource://firefox-at-hypothes-dot-is/hypothesis/data

At this point, a working extension should exist in either ``./build/chrome``
or ``./build/firefox`` but with the development configuration the static assets
are still loaded from the server. Start the application and ensure that the
assets are built by visiting the home page or by running
``./bin/hypothesis assets``.

Note: Bundling the assets in the extension only works at the moment when the
``webassets.debug`` setting is falsy.

Deployment
----------

Heroku
^^^^^^

The project is set up to run out of the box on Heroku using these add-ons:

- Heroku PostgreSQL
- Mailgun, Mandrill, or SendGrid for sending e-mail
- RedisToGo for session storage

Docker
^^^^^^

The following docker link names are supported for automatic configuration of
services:

- ``elasticsearch``
- ``mail``
- ``nsqd``
- ``redis``
- ``statsd``

Manual
^^^^^^

The following shell environment variables are supported:

- ``CLIENT_ID`` a unique API key for authentication
- ``CLIENT_SECRET`` a unique API secret for signing authentication requests
- ``DATABASE_URL`` in the format used by Heroku
- ``ELASTICSEARCH_INDEX`` the Elasticsearch index for annotation storage
- ``MAIL_DEFAULT_SENDER`` a sender address for outbound mail
- ``SECRET_KEY`` a unique string secret

Customized embedding
--------------------

By default, Hypothesis instantiates the ``Annotator.Host`` class defined in
the injected code loaded by ``embed.js``. It is possible to change this by
assigning an alternate constructor to ``window.hypothesisRole``. To customize
the plugins that are loaded, define a function ``window.hypothesisConfig`` which
returns an options object. This is then passed to the constructor as the
second argument::

    window.hypothesisConfig = function () {
      return {
        app: 'https://example.com/custom_sidebar_iframe',
        Toolbar: {container: '.toolbar-wrapper'}
      };
    };

With the exception of ``app``, the properties for the options object are the
names of Annotator plugins and their values are the options passed to the
individual plugin constructors.

The ``app`` property should be a url pointing to the HTML document that will be
embedded in the page.

The full range of possibilities here is still in need of documentation and we
would appreciate any help to improve that.


Documentation
--------------------------

To build the documentation, ensure that Sphinx_ is installed and issue the
```make html``` command from the docs directory::

    $ cd docs/
    $ make html

License
-------

Hypothesis is released under the `2-Clause BSD License`_, sometimes referred
to as the "Simplified BSD License" or the "FreeBSD License". Some third-party
components are included. They are subject to their own licenses. All of the
license information can be found in the included `<LICENSE>`_ file.

.. [*] Community and identity features are not finished. Get involved and help!
.. _Open Annotation Core: http://openannotation.org/spec/core/
.. _project wiki: https://github.com/hypothesis/h/wiki
.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode: http://freenode.net/
.. _subscribe: mailto:dev+subscribe@list.hypothes.is
.. _development mailing list: http://list.hypothes.is/archive/
.. _New Contributor Friendly: https://github.com/hypothesis/h/issues?q=is%3Aopen+is%3Aissue+label%3A%22New+Contributor+Friendly%22
.. _contributing: CONTRIBUTING.rst
.. _Annotator project: http://okfnlabs.org/projects/annotator/
.. _Open Knowledge Foundation: http://okfn.org/
.. _2-Clause BSD License: http://www.opensource.org/licenses/BSD-2-Clause
.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. _pyramid_debugtoolbar documentation: http://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/
.. _Sphinx: http://sphinx-doc.org/

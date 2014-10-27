Hypothes.is
===========

.. image:: https://travis-ci.org/hypothesis/h.svg?branch=master
   :target: https://travis-ci.org/hypothesis/h
   :alt: Build Status

About
-----

Hypothes.is brings community peer review to The Internet. It is a web
application which enables rich annotation of web content. The project acts as
a community aggregator for annotations and identity provider [*]_ for
annotators. It also serves embed code for an annotation agent designed with
modern web browsers in mind.

Installation
------------

See `<INSTALL.rst>`_ for installation instructions. Platform specific
instructions can be found in the install documents as well.

Running
-------

Installation has, hopefully, gone smoothly. If you ran into any problems, be
sure to seek help on IRC or the mailing list. To run the server, simply use
the ``run`` command::

    $ ./run

This command will start the server on port 5000 (http://localhost:5000),
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

See the `project wiki`_ for the roadmap and additional information and
join us in `#hypothes.is`_ on freenode_ for discussion.

Those wishing to contribute to the project should also `subscribe`_ to the
development mailing list and read about `contributing`_. Then consider getting
started on one of the issues that are ready for work. Issues tagged with the
label 'New Contributor Friendly' are ideal for those just getting started.

Debugging
---------

The `debugtoolbar`_ package is loaded by default in the development
environment.  This will provide stack traces for exceptions and allow basic
debugging. A more advanced profiler can also be accessed at the /_debug_toolbar
path.

    http://localhost:5000/_debug_toolbar/

Check out the documentation for information on how to use and configure it.

Testing
-------

To run the test suite, ensure the assets are built and then invoke the tests
in the usual fashion of Python::

    $ ./bin/python setup.py test

As a convenience, there is a make target for this::

    $ make test

Chrome Extension
^^^^^^^^^^^^^^^^
Run the following command at the prompt to build the extension::

    $ ./bin/hypothesis extension development.ini http://localhost:5000

If you are managing your virtual environment yourself, the script may not be
located in the ``bin`` directory, but should be available in your path when the
virtual environment is activated.

The third argument is the base URL for the application. An optional, fourth
argument may be passed to override the URL prefix used for static assets.

At this point, a working extension should exist in ./build/chrome but with
the development configuration the static assets are still loaded from the
server. Start the application and ensure that the assets are built by visiting
the home page or by running ``./bin/hypothesis assets``.

Note: Bundling the assets in the extension only works at the moment when the
``webassets.debug`` setting is falsy.

Deployment
----------

Deployment is mostly left as an exercise to the reader until we document this
better. Using `Docker`_ or the shell environment it is easy to customize a few
different deployment options.

Docker links
^^^^^^^^^^^^

The following docker link names are supported for automatic configuration of
services:

- ``elasticsearch``
- ``mail``
- ``redis``
- ``statsd``

Shell environment
^^^^^^^^^^^^^^^^^

The following shell environment variables are supported:

- ``DATABASE_URL`` in the format used by Heroku
- ``SESSION_SECRET`` a unique string secret for cookie validation

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

Hypothes.is is released under the `2-Clause BSD License`_, sometimes referred
to as the "Simplified BSD License" or the "FreeBSD License". Some third-party
components are included. They are subject to their own licenses. All of the
license information can be found in the included `<LICENSE>`_ file.

.. [*] Community and identity features are not finished. Get involved and help!
.. _Open Annotation Core: http://openannotation.org/spec/core/
.. _project wiki: https://github.com/hypothesis/h/wiki
.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode: http://freenode.net/
.. _subscribe: mailto:dev+subscribe@list.hypothes.is
.. _contributing: CONTRIBUTING.rst
.. _Annotator project: http://okfnlabs.org/projects/annotator/
.. _Open Knowledge Foundation: http://okfn.org/
.. _2-Clause BSD License: http://www.opensource.org/licenses/BSD-2-Clause
.. _debugtoolbar: http://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/
.. _Sphinx: http://sphinx-doc.org/

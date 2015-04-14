Hacking guide
#############

This document contains instructions on setting up a development environment for
h. If you are looking for instructions on deploying h in a production
environment, please consult :doc:`INSTALL` instead.

For developing h, you will need the following tools and libraries installed:

-  Python_ v2.7
-  Node_ v0.10+ and its package manager, npm
-  Compass_ v1.0+

In addition, you will need to run, at a minimum, the following external
services:

-  ElasticSearch_ v1.0+, with the `ElasticSearch ICU Analysis`_ plugin
   installed
-  NSQ_ v0.3+

.. _Python: http://python.org/
.. _Node: http://nodejs.org/
.. _Compass: http://compass-style.org/
.. _ElasticSearch: http://www.elasticsearch.org/
.. _ElasticSearch ICU Analysis: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/analysis-icu-plugin.html
.. _NSQ: http://nsq.io/


Prerequisites
-------------

Installing h's system dependencies requires different approaches on different
platforms. Pick a document below for your platform and follow the instructions.

.. toctree::
   :maxdepth: 1
   :glob:

   HACKING.*

Next, install and configure ElasticSearch. Follow the :doc:`instructions on
setting up ElasticSearch <elasticsearch>`. Make sure ElasticSearch is running.

Finally, the NSQ homepage has `instructions on installing NSQ`_. Once installed,
running ``nsqd`` in its default configuration should suffice for integration
with h in a development environment.

.. _instructions on installing NSQ: http://nsq.io/deployment/installing.html


Getting started
---------------

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

.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.org/en/latest/install.html


Running
-------

Once platform dependencies are installed::

    $ make deps

This will install the rest of the libraries needed for the application. Then::

    $ make dev

This will start the server on port 5000 (http://localhost:5000), reload the
application whenever changes are made to the source code, and restart it should
it crash for some reason.

.. note::
    Using the bookmarklet or otherwise embedding the application may not
    be possible on sites accessed via HTTPS due to browser policy restricting
    the inclusion of non-SSL content.


Debugging
---------

The `pyramid_debugtoolbar`_ package is loaded by default in the development
environment.  This will provide stack traces for exceptions and allow basic
debugging. A more advanced profiler can also be accessed at the /_debug_toolbar
path.

    http://localhost:5000/_debug_toolbar/

Check out the `pyramid_debugtoolbar documentation`_ for information on how to
use and configure it.

.. _pyramid_debugtoolbar: https://github.com/Pylons/pyramid_debugtoolbar
.. _pyramid_debugtoolbar documentation: http://docs.pylonsproject.org/projects/pyramid-debugtoolbar/en/latest/


Testing
-------

There are test suites for both the frontend and backend code.

To run the Python suite, invoke the tests in the standard fashion::

    $ python setup.py test

To run the JavaScript suite, run::

    $ $(npm bin)/karma start h/static/scripts/karma.config.js --single-run

As a convenience, there is a make target which will do all of the above::

    $ make test


Browser extensions
------------------

To build the browser extensions, use the ``hypothesis-buildext`` tool::

    usage: hypothesis-buildext [-h] config_uri {chrome,firefox} ...

    positional arguments:
      config_uri        paster configuration URI

    optional arguments:
      -h, --help        show this help message and exit

    browser:
      {chrome,firefox}
        chrome          build the Google Chrome extension
        firefox         build the Mozilla Firefox extension

At this point, a working extension should exist in either ``./build/chrome``
or ``./build/firefox``. If the development configuration was used, static
assets are loaded from the server. Start the application and ensure that the
assets are built by visiting the start page or by running the ``assets``
command::

    usage: hypothesis assets [-h] config_uri

    positional arguments:
      config_uri  paster configuration URI

    optional arguments:
      -h, --help  show this help message and exit


Code quality
------------

We run a variety of analysis tools on the python codebase using the prospector
package. This is run by the CI on each push but can also be run manually
via the ``lint`` make command::

    $ make lint


Documentation
-------------

To build the documentation, ensure that Sphinx_ is installed and issue the
```make html``` command from the docs directory::

    $ cd docs/
    $ make html

.. _Sphinx: http://sphinx-doc.org/


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


Serving h over SSL in development
---------------------------------

If you want to annotate a site that's served over https then you'll need to
serve h over https as well, otherwise the browser will refuse to launch h and
give a mixed-content warning.

To serve your local dev instance of h over https:

1. Generate a private key and certificate signing request::

    openssl req -newkey rsa:1024 -nodes -keyout key.pem -out req.pem

2. Generate a self-signed certificate::

    openssl x509 -req -in req.pem -signkey key.pem -out server.crt

3. Run ``gunicorn`` with the ``certfile`` and ``keyfile`` options::

    gunicorn --reload --paste conf/development.ini --certfile=server.crt --keyfile=key.pem

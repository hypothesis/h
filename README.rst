Hypothes.is
###########

About
-----

Hypothes.is brings community peer review to The Internet. It is a web site
and a browser application which enable rich annotation of web content. The
web site acts as both a community and authentication end point as well as a
deployment host for the browser application.

The browser application is based substantially on work by the `Open Knowledge
Foundation`_ on the `Annotator Project`_.

Please join us in `#hypothes.is`_ on freenode_.

Installation
------------

Hypothes.is currently requires several tools to build and run from scratch.
In the future, releases will include built versions of static assets for
integrators wanting to produce custom embeddings of the project on their
own sites and the project welcomes packaging efforts to make including
the Hypothes.is service in any framework easy.

The project code itself is a pyramid_ application which can be integrated
into any WSGI_ compatible framework and run on any WSGI web server (such
as gunicorn_ or uWSGI_). Until the project is ready for an alpha release,
it may not be installable from the Python Package Index. Instead, the
application should be built in a virtual environment which can be set up as
follows::

    $ virtualenv --no-site-packages .
    $ source bin/activate
    $ pip install -r requirements.txt

If there is a failure installing PyYAML, install the libyaml development files.

For building the static assets, requirements currently include CoffeeScript_
(needed by the Annotator), Sass_, Compass_ and Handlebars_. These dependencies
should be easily installable via common package management utilities.

For production use, the application can also be configured to use UglifyJS_ and
clean-css_ for minification needs. These are *not* required for development.

To run an annotation storage backend elasticsearch_ is required.

Please see the platform-specific INSTALL files for additional assistance.

Development
-----------

See `#hypothes.is`_.

License
-------

Hypothes.is is released under the `2-Clause BSD License`_, sometimes referred
to as the "Simplified BSD License" or the "FreeBSD License". Some third-party
components are included. They are subject to their own licenses. All of the
license information can be found in the included LICENSE file.

.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode: http://freenode.net/
.. _Annotator project: http://okfnlabs.org/annotator/
.. _Open Knowledge Foundation: http://okfn.org/
.. _pyramid: http://www.pylonsproject.org/
.. _gunicorn: http://gunicorn.org/
.. _uWSGI: http://projects.unbit.it/uwsgi/
.. _elasticsearch: http://www.elasticsearch.org/
.. _CoffeeScript: http://coffeescript.org/
.. _Sass: http://sass-lang.com/
.. _Compass: http://compass-style.org/
.. _Handlebars: http://handlebarsjs.com/
.. _UglifyJS: http://marijnhaverbeke.nl//uglifyjs
.. _clean-css: https://github.com/GoalSmashers/clean-css
.. _2-Clause BSD License: http://www.opensource.org/licenses/BSD-2-Clause

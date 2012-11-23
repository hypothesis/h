Installing Hypothes.is
######################

Hypothes.is currently requires several tools to build and run from scratch.

See the platform specific INSTALL.<whatever>.rst files for more information
about how to install the dependencies on any specific platform.

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
    $ python setup.py develop
    $ pip install -r requirements.txt

If there is a failure installing PyYAML, install the libyaml development files.

For building the static assets, requirements currently include CoffeeScript_
(needed by the Annotator), Sass_, Compass_ and Handlebars_. These dependencies
should be easily installable via common package management utilities.

For production use, the application can also be configured to use UglifyJS_ and
clean-css_ for minification needs. These are *not* required for development.

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

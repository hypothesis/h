Installing
######################

Dependencies:

* Python v2.7+ (No Python 3 support yet -- want to help?)
* CoffeeScript_ v1.6+
* Sass_ v3.2+
* Compass_ v0.12+
* ElasticSearch_ v0.19+

See the platform specific ``INSTALL.<platform>.rst`` files for more information
about how to install the dependencies on any specific platform (see below).

In the future, releases will include built versions of static assets which
will eliminate the need for those who wish to integrate with their own
Python web services but do not need to modify the front-end sources.

The project code itself is a pyramid_ application which can be integrated
into any WSGI_ compatible framework and run on any WSGI web server (such
as gunicorn_ or uWSGI_). Until the project is ready for general testing
it will not be installable from the Python Package Index. Instead, the
application should be built in a virtual environment which can be set up as
follows:

.. code-block:: bash

    ./bootstrap

The command will set up the development environment and check for development
dependencies. Warnings will be issued for missing dependencies. When this
script runs successfully, the environment should be prepared. It is good
practice to run this script whenever the source code changes, such as after
pulling new commits from upstream, or checking out a new branch, which may
have changed (for example: updated) requirements.

For building the static assets, requirements currently include CoffeeScript_
and Sass_ with Compass_ installed. These tools are widely available in package
repositories. Check the platform-specific installation instructions for
details.

For production use, the application will use UglifyJS_ and clean-css_ for
minification needs. These are not required when running the project in a
development configuration.

Platform Specific Instructions
------------------------------

Platform specific instructions currently exist for the following platforms:

* ArchLinux_
* Debian_
* Fedora_
* OSX_
* Ubuntu_
* Vagrant_ (contains information for installing on Windows)

Feel free to add a section for a new platform, particularly if you think it
may be a niche use case. Pull requests which create an
``Install.<Platform>.rst`` are preferred. And of course, edits to existing
docs should be done in a pull request.

.. _pyramid: http://www.pylonsproject.org/
.. _WSGI: http://www.wsgi.org/
.. _gunicorn: http://gunicorn.org/
.. _uWSGI: http://projects.unbit.it/uwsgi/
.. _ElasticSearch: http://www.elasticsearch.org/
.. _CoffeeScript: http://coffeescript.org/
.. _Sass: http://sass-lang.com/
.. _Compass: http://compass-style.org/
.. _UglifyJS: http://marijnhaverbeke.nl//uglifyjs
.. _clean-css: https://github.com/GoalSmashers/clean-css
.. _ArchLinux: INSTALL.ArchLinux.rst
.. _Debian: INSTALL.Debian.rst
.. _Fedora: INSTALL.Fedora.rst
.. _OSX: INSTALL.OSX.rst
.. _Ubuntu: INSTALL.Ubuntu.rst
.. _Vagrant: INSTALL.Vagrant.rst

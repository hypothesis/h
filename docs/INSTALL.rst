Installing
######################

Dependencies:

* Python v2.7+ (No Python 3 support yet -- want to help?)
* CoffeeScript_ v1.6+
* Sass_ v3.2+
* Compass_ v0.12+
* ElasticSearch_ v1.0+
* `ElasticSearch ICU Analysis`_ plugin

Platform Specific Instructions
------------------------------

To install the dependencies on any specific platform, follow the instructions in one of the following files (see below).

* ArchLinux_
* Debian_
* Fedora_
* OSX_
* Ubuntu_

Feel free to add instructions for a new platform in a file named
``Install.<Platform>.rst`` particularly if you think it
may be a niche use case. Contributions (and updates) to the other install
instruction files are *very* welcome.

General Instructions
--------------------

Once the basic dependencies are installed, the `ElasticSearch ICU Analysis`_
plugin is needed. Follow the instructions_ available from that project.

The project code itself is a pyramid_ application which can be integrated
into any WSGI_ compatible framework and run on any WSGI web server, such as
as gunicorn_ or uWSGI_. However, at this time support for the WebSocket
protocol assumes gunicorn.

For building the static assets, requirements currently include CoffeeScript_
and Sass_ with Compass_ installed. CoffeeScript will be installed for you but
Sass and Compass must be installed manually. These tools are widely available
in package repositories. Check the platform-specific installation instructions
for details.

For production use, the application will use UglifyJS_ and clean-css_ for
minification needs. These are not required when running the project in a
development configuration but will be installed locally.

In the future, releases will include built versions of static assets which
will eliminate the need for those who wish to integrate with their own
Python web services but do not need to modify the front-end sources.

Troubleshooting
---------------

By default, ElasticSearch may try to join other nodes on the network resulting
in ``IndexAlreadyExists`` errors at startup. See the documentation for how to
turn off discovery.

.. _pyramid: http://www.pylonsproject.org/
.. _WSGI: http://www.wsgi.org/
.. _gunicorn: http://gunicorn.org/
.. _uWSGI: http://projects.unbit.it/uwsgi/
.. _ElasticSearch: http://www.elasticsearch.org/
.. _ElasticSearch ICU Analysis: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/analysis-icu-plugin.html
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
.. _instructions: http://www.elasticsearch.org/guide/en/elasticsearch/guide/master/icu-plugin.html

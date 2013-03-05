Installing Hypothes.is on Ubuntu Server 12.04.1 LTS
######################

To install the dependencies, run these commands::

    $ sudo apt-get install python-{dev,pip,virtualenv} ruby-compass coffeescript npm git libpq-dev

This will install almost anything you need for development.

The project code itself is a pyramid_ application which can be integrated
into any WSGI_ compatible framework and run on any WSGI web server (such
as gunicorn_ or uWSGI_). Until the project is ready for an alpha release,
it may not be installable from the Python Package Index. Instead, the
application should be built in a virtual environment which can be set up as
follows::

    $ ./bootstrap

The command will set up the development environment and check for development
dependencies. Warnings will be issued for missing dependencies. When this
script runs without successfully, the environment should be prepared. It is
good practice to run this script whenever the source code changes, such as
after pulling new commits from upstream or checking out a new branch that may
have changed (for example: updated) requirements.

The only thing you need to install manually is elasticsearch_,
which is required to run the application.

Before installing elastisearch_, you need some JRE, for example:

    $ sudo apt-get install openjdk-7-jre

To quickest way to install elastisearch is to simply install elasticsearchdeb_.

Run the elasticsearch from the directory where you've cloned the repository. You can 
run it with the following::

    $ bin/elasticsearch -f

Once you have successfully installed the requirements, you'll be able to start 
the server with::

    $ ./run

For building the static assets, requirements currently include CoffeeScript_
and Sass_ with Compass_ installed. These tools are widely available in package
repositories. Check the platform-specific installation instructions for
details.

For production use, the application will use UglifyJS_ and clean-css_ for
minification needs. These are not required when running the project in a
development configuration.


.. _pyramid: http://www.pylonsproject.org/
.. _gunicorn: http://gunicorn.org/
.. _uWSGI: http://projects.unbit.it/uwsgi/
.. _elasticsearch: http://www.elasticsearch.org/
.. _CoffeeScript: http://coffeescript.org/
.. _Sass: http://sass-lang.com/
.. _Compass: http://compass-style.org/
.. _UglifyJS: http://marijnhaverbeke.nl//uglifyjs
.. _clean-css: https://github.com/GoalSmashers/clean-css
.. _elasticsearch: http://www.elasticsearch.org/
.. _elasticsearchdeb: https://github.com/downloads/elasticsearch/elasticsearch/elasticsearch-0.19.11.deb


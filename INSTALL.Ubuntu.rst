Installing Hypothes.is on Ubuntu Server 12.04.1 LTS
######################

To install the dependencies, run these commands::

    $ sudo apt-get install python-{dev,pip,virtualenv} ruby-compass coffeescript npm git libpq-dev

This will install almost everything you need for development.

The only thing you need to install manually is elasticsearch_,
which is required to run the application.

Before installing elastisearch_, you need some JRE, for example:

    $ sudo apt-get install openjdk-7-jre

To quickest way to install elastisearch is to simply install elasticsearchdeb_.

Run the elasticsearch from the directory where you've cloned the repository. You can 
run it with the following::

    $ bin/elasticsearch -f

Further instructions can be found in INSTALL.rst

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


Installing Hypothes.is on Debian
######################

Currently (november 2012), the required packages are not part of the stable
distribution; you need to fetch some stuff from the unstable ditribution.

To install the dependencies, run these commands::

    $ sudo apt-get install python-{pip,virtualenv} ruby-{compass,coffee-script} coffeescript libjs-coffeescript npm
    $ sudo npm install -g handlebars

This will install almost anything you need for development.
The only thing you need to install manually is elasticsearch_,
which is required to run the application.

After installing the above, create the virtualenv,
as described in the README.rst

(Run the commands from the directory where you've cloned the repository.)

.. _elasticsearch: http://www.elasticsearch.org/

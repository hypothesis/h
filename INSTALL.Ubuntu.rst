Installing Hypothes.is on Ubuntu Server 12.04.2 LTS
######################

To install the dependencies, run these commands:

.. code-block:: bash

    sudo apt-get install build-essential git libyaml-dev
    sudo apt-get install python-{dev,pip,virtualenv} ruby-compass

You will need the latest Node:

.. code-block:: bash

    sudo add-apt-repository ppa:chris-lea/node.js
    sudo apt-get update
    sudo apt-get install nodejs

And the latest version of CoffeeScript:

.. code-block:: bash

    sudo npm install --global coffee-script

This will install almost anything you need for development.
The only thing you need to install manually is elasticsearch_,
which is required to run the application.

Before installing elastisearch_, you need a JRE, for example:

.. code-block:: bash

    sudo apt-get install openjdk-7-jre

The quickest way to install elastisearch is to simply install the deb package:

.. code-block:: bash

    wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-0.20.5.deb
    sudo dpkg -i elasticsearch-0.20.5.deb

After installing the above, continue along in the INSTALL.rst

.. _elasticsearch: http://www.elasticsearch.org/

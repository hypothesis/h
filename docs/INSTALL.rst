Installation guide
##################

This document contains instructions for deploying h to a production environment.
If you are looking for instructions on setting up a development environment for
h, please consult :doc:`HACKING` instead.

h is deployed exclusively as a Docker_ container. This allows the development
team to focus their efforts on developing for a single, consistent environment.
It also means that across a wide variety of platforms (those support by Docker
itself) the instructions for configuring and deploying h are identical.

In addition to the Docker container, h depends on the following services:

-  An SQL database. We only officially support PostgreSQL_.
-  ElasticSearch_ v1.0+, with the `ElasticSearch ICU Analysis`_ plugin
   installed. Used for storing annotation data.
-  NSQ_, a distributed message queue. Used for interprocess communication.
-  Redis_, a fast key-value store. Used for persistent session storage.

.. _Docker: https://www.docker.com/
.. _PostgreSQL: http://www.postgresql.org/
.. _ElasticSearch: https://www.elastic.co/products/elasticsearch
.. _ElasticSearch ICU Analysis: https://github.com/elastic/elasticsearch-analysis-icu
.. _NSQ: http://nsq.io/
.. _Redis: http://redis.io/


Prerequisites
-------------

You will need to have installed and configured Docker (v1.4 or greater) in order
to deploy h. Please follow `the Docker team's instructions on how to install
Docker`_.

.. _the Docker team's instructions on how to install Docker: https://docs.docker.com/installation/


Building the image
------------------

We do not currently publish a built image for h. You must build the base image
for h by running the following from the root of the repository::

    $ docker build -t hypothesis/h .

This will take some time to complete, as it will install and configure a
complete image of h and all its direct dependencies.


Running the container
---------------------

You can now run a Docker container using the ``hypothesis/h`` image you just
built. At its simplest, this consists of running::

    $ docker run hypothesis/h

but this will usually result in a container which is missing some important
configuration. In particular, you need to let the running h instance know where
its external service dependencies are. This is most easily done by configuring
one or more of the following Docker link names, which will result in automatic
configuration of these services:

-  ``elasticsearch``
-  ``mail``
-  ``nsqd``
-  ``redis``
-  ``statsd``

In a production environment you should set the following container environment
variables:

-  ``APP_URL`` the base URL of the application
-  ``DATABASE_URL`` an SQLAlchemy compatible database URL
-  ``SECRET_KEY`` a secret key for use in cryptographic operations

.. note::
   You can generate an appropriate secret key as follows::

       $ python -c 'import base64; import os; print(base64.b64encode(os.urandom(64))).strip(b"=")'

You will probably also want to set one or more of the following configuration
options:

- ``ALLOWED_ORIGINS`` origins allowed to connect over the WebSocket protocol
- ``CLIENT_ID`` a unique API key for authentication
- ``CLIENT_SECRET`` a unique API secret for signing authentication requests
- ``ELASTICSEARCH_INDEX`` the ElasticSearch index name for annotation storage
- ``MAIL_DEFAULT_SENDER`` a sender address for outbound mail
- ``WEBASSETS_BASE_DIR`` the base directory for static assets
- ``WEBASSETS_BASE_URL`` the base URL for static asset routes

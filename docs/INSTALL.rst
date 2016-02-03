Deploying to a production environment
#####################################

This document contains instructions for deploying h to a production environment.
If you are looking for instructions on setting up a development environment for
h, please consult :doc:`/hacking/index` instead.

h is deployed exclusively as a Docker_ container. This allows the development
team to focus their efforts on developing for a single, consistent environment.
It also means that across a wide variety of platforms (those support by Docker
itself) the instructions for configuring and deploying h are identical.

In addition to the Docker container, h depends on the following services:

-  An SQL database. We only officially support PostgreSQL_.
-  Elasticsearch_ v1.0+, with the `Elasticsearch ICU Analysis`_ plugin
   installed. Used for storing annotation data.
-  NSQ_, a distributed message queue. Used for interprocess communication.
-  Redis_, a fast key-value store. Used for persistent session storage.

.. _Docker: https://www.docker.com/
.. _PostgreSQL: http://www.postgresql.org/
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
.. _Elasticsearch ICU Analysis: https://github.com/elastic/elasticsearch-analysis-icu
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

The Hypothesis team builds and publishes a Docker image,
``hypothesis/hypothesis`` to `the Docker hub`_. You can pull and use this image
with::

    $ docker pull hypothesis/hypothesis

In some cases you may wish to build the image yourself, which you can do with a
command such as the following from the root of the git repository::

    $ git archive HEAD | docker build -t hypothesis/hypothesis -

This will take some time to complete, as it will install and configure a
complete image of h and all its direct dependencies.

.. _the Docker hub: https://hub.docker.com/r/hypothesis/hypothesis/


Configuring container dependencies
----------------------------------

At a minimum, you will need:

-  a PostgreSQL database
-  an Elasticsearch server with the ICU analysis plugin enabled
-  an nsqd server
-  a Redis server
-  a mailer

One option is to containerise these services, although you should investigate
for yourself if this is a sensible approach for your environment.

For example, we choose to run Elasticsearch, nsqd, and Redis in containers. We
also use an `ambassador container`_ to point to our mailserver::

    $ docker run -d --name elasticsearch nickstenning/elasticsearch-icu
    $ docker run -d --name nsqd --expose 4150 --expose 4151 nsqio/nsq /nsqd
    $ docker run -d --name redis redis
    $ docker run -d --name mail --expose 25 -e MAIL_PORT_25_TCP=tcp://smtp.mydomain.com:25 svendowideit/ambassador

And configure a PostgreSQL database identified by the following `SQLAlchemy
database URL`_::

    postgresql://scott:tiger@dbserver/mydatabase

.. _ambassador container: https://docs.docker.com/articles/ambassador_pattern_linking/
.. _SQLAlchemy database URL: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls


Running the container
---------------------

You can run a Docker container using the ``hypothesis/hypothesis`` image. At its
simplest, this consists of running::

    $ docker run -d -p 5000:5000 hypothesis/hypothesis

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

Using the example given in the previous section, in which we started containers
for our external services, we can use `docker links`_ to configure the h
container::

    $ docker run -d -p 5000:5000 \
                 -e DATABASE_URL=postgresql://scott:tiger@dbserver/mydatabase \
                 --link elasticsearch:elasticsearch \
                 --link nsqd:nsqd \
                 --link redis:redis \
                 --link mail:mail \
                 hypothesis/hypothesis

.. _docker links: https://docs.docker.com/userguide/dockerlinks/

Please note that in a production environment there are several additional steps
you should take. First, there are several important environment variables you
should set:

-  ``APP_URL`` the base URL of the application
-  ``SECRET_KEY`` a secret key for use in cryptographic operations

.. note::
   You can generate an appropriate secret key as follows::

       $ python -c 'import base64; import os; print(base64.b64encode(os.urandom(64))).strip(b"=")'

You will probably also want to set one or more of the following configuration
options:

- ``ALLOWED_ORIGINS`` origins allowed to connect over the WebSocket protocol
- ``CLIENT_ID`` a unique API key for authentication
- ``CLIENT_SECRET`` a unique API secret for signing authentication requests
- ``ELASTICSEARCH_INDEX`` the Elasticsearch index name for annotation storage
- ``MAIL_DEFAULT_SENDER`` a sender address for outbound mail
- ``WEBASSETS_BASE_DIR`` the base directory for static assets
- ``WEBASSETS_BASE_URL`` the base URL for static asset routes

In addition, there are several important components of a production Hypothesis
installation which will need to be run in their own containers. For example,
worker processes::

    $ docker run --name h-worker-notification \
                 [...additional config...] \
                 hypothesis/hypothesis \
                 hypothesis-worker conf/app.ini notification
    $ docker run --name h-worker-nipsa \
                 [...additional config...] \
                 hypothesis/hypothesis \
                 hypothesis-worker conf/app.ini nipsa

And, possibly, a websocket server::

    $ docker run --name h-websocket \
                 [...additional config...] \
                 -p 5001:5001 \
                 hypothesis/hypothesis \
                 gunicorn --paste conf/websocket.ini

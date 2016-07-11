Hypothesis dev install
======================

These sections tell you how to install Hypothesis in a development environment.

Hypothesis is built from two main codebases:

1. The code for the https://hypothes.is/ website itself, which lives in a
   `Git repo named h`_. This includes an HTTP API for fetching and saving
   annotations.

2. The code for the Hypothesis annotation client (the sidebar), which lives in
   a `Git repo named client`_. The client sends HTTP requests to the web
   service to fetch and save annotations.

If you just want to work on the https://hypothes.is/ website and API then
you can just follow the :doc:`website` section, your development site will
automatically use a `built copy of the Hypothesis client from npm`_.

If you want to work on the Hypothesis client code then you need development
installs of both the website/API *and* the client.
First follow :doc:`website` then :doc:`client`.


.. toctree::

   website
   client

.. include:: targets.rst

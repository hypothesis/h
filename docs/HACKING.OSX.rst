Mac OS X system dependencies
############################

This document describes how to install dependencies for an h development
environment on Mac OS X. **NB:** You do not need to follow these instructions if
deploying a production instance of h: see :doc:`INSTALL` instead.

The instructions that follow assume you have previously installed Homebrew_.

.. _Homebrew: http://brew.sh/

Install the following packages::

    $ brew install \
        libevent \
        libffi \
        libyaml \
        node \
        python

Install compass::

    $ gem install compass

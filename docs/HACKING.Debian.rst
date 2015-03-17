Debian/Ubuntu system dependencies
#################################

This document describes how to install dependencies for an h development
environment on Debian and Debian-like GNU/Linux distributions (such as Ubuntu).
**NB:** You do not need to follow these instructions if deploying a production
instance of h: see :doc:`INSTALL` instead.

Not all required packages are necessarily part of the ``stable`` distribution;
you may need to fetch some stuff from ``unstable``. (On Ubuntu, you may need to
add the ``universe`` package repositories.)

Install the following packages::

    $ apt-get -y --no-install-recommends \
        build-essential \
        git \
        libevent-dev \
        libffi-dev \
        libpq-dev \
        libyaml-dev \
        nodejs \
        npm \
        python-dev \
        python-pip \
        python-virtualenv \
        ruby \
        ruby-dev

Upgrade pip and npm::

    $ pip install -U pip virtualenv
    $ npm install -g npm

Install compass::

    $ gem install compass

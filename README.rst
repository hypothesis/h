Hypothes.is
###########

About
-----

Hypothes.is brings community peer review to The Internet. It is a web
application which enables rich annotation of web content. The project acts as
a community aggregator for annotations and identity provider [*]_ for
annotators. It also serves embed code for an annotation agent designed with
modern web browsers in mind.

Installation
------------

See `<INSTALL.rst>`_ for installation instructions.

Running
-------

Installation has, hopefully, gone smoothly. If you ran into any problems, be
sure to seek help on IRC or the mailing list. To run the server, simply use
the ``run`` command::

    $ ./run

This command will start the server on port 5000 (https://0.0.0.0:5000),
reload the application whenever changes are made to the source code, and
restart it should it crash for some reason.

.. note::
    Using the bookmarklet or otherwise embedding the application may not
    be possible on sites accessed via HTTPS due to browser policy restricting
    the inclusion of non-SSL content. If you wish to test the development server
    with these sites uncomment the line beginning with "certfile" in the
    development server configuration file, "development.ini". This will cause
    the server to use a self-signed certificate included for testing.

Development
-----------

The project builds heavily on components developed for the `Annotator Project`_
and is structured to encourage upstream contribution where possible. However,
work is required to make Annotator more extensible in order to facilitate
contribution.

Additionally, work is underway to support the data model described by the
`Open Annotation Core`_ specification document.

See the `project wiki`_ for the roadmap and additional information and
join us in `#hypothes.is`_ on freenode_ for discussion.

Those wishing to contribute to the project should also `subscribe`_ to the
development mailing list and read about `contributing`_. Then consider getting
started on one of the issues that are ready for work by clicking on the badge
below. Issues tagged with the label 'cake' are ideal for new contributors.

.. image:: http://badge.waffle.io/hypothesis/h.png
   :target: http://waffle.io/hypothesis/h
   :alt: Stories in Ready
   :align: left
   :height: 18px
.. image:: https://travis-ci.org/hypothesis/h.png?branch=develop
   :target: https://travis-ci.org/hypothesis/h
   :alt: Build Status
   :height: 18px

Chrome Extension
^^^^^^^^^^^^^^^^
To build the Chrome extension, follow the installation instructions. Then,
run the following command at the prompt::

    $ ./bin/hypothesis extension development.ini http://localhost:5000/app

If you are managing your virtual environment yourself, the script may not be
located in the ``bin`` directory, but should be available in your path when the
virtual environment is activated.

The third argument is the base URL for the application. An optional, fourth
argument may be passed to override the URL prefix used for static assets.

License
-------

Hypothes.is is released under the `2-Clause BSD License`_, sometimes referred
to as the "Simplified BSD License" or the "FreeBSD License". Some third-party
components are included. They are subject to their own licenses. All of the
license information can be found in the included `<LICENSE>`_ file.

.. [*] Community and identity features are not finished. Get involved and help!
.. _Open Annotation Core: http://openannotation.org/spec/core/
.. _project wiki: https://github.com/hypothesis/h/wiki
.. _#hypothes.is: http://webchat.freenode.net/?channels=hypothes.is
.. _freenode: http://freenode.net/
.. _subscribe: mailto:dev+subscribe@list.hypothes.is
.. _contributing: CONTRIBUTING.rst
.. _Annotator project: http://okfnlabs.org/annotator/
.. _Open Knowledge Foundation: http://okfn.org/
.. _2-Clause BSD License: http://www.opensource.org/licenses/BSD-2-Clause
